
import time

from boto3 import session
from botocore import exceptions

from hypernet_agentless.common import hs_constants
from hypernet_agentless.server.extensions import hyperswitch
from hypernet_agentless.server.services.hyperswitch import provider_api

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


AWS_STATUS = {
    'pending': '0',
    'running': '16',
    'shutting-down': '32',
    'terminated': '48',
    'stopping': '64',
    'stopped': '80',
}


MAX_NIC = {
    'c1.medium': 2,
    'c1.xlarge': 4,
    'c3.large': 3,
    'c3.xlarge': 4,
    'c3.2xlarge': 4,
    'c3.4xlarge': 8,
    'c3.8xlarge': 8,
    'c4.large': 3,
    'c4.xlarge': 4,
    'c4.2xlarge': 4,
    'c4.4xlarge': 8,
    'c4.8xlarge': 8,
    'cc2.8xlarge': 8,
    'cg1.4xlarge': 8,
    'cr1.8xlarge': 8,
    'd2.xlarge': 4,
    'd2.2xlarge': 4,
    'd2.4xlarge': 8,
    'd2.8xlarge': 8,
    'g2.2xlarge': 4,
    'g2.8xlarge': 8,
    'hi1.4xlarge': 8,
    'hs1.8xlarge': 8,
    'i2.xlarge': 4,
    'i2.2xlarge': 4,
    'i2.4xlarge': 8,
    'i2.8xlarge': 8,
    'm1.small': 2,
    'm1.medium': 2,
    'm1.large': 3,
    'm1.xlarge': 4,
    'm2.xlarge': 4,
    'm2.2xlarge': 4,
    'm2.4xlarge': 8,
    'm3.medium': 2,
    'm3.large': 3,
    'm3.xlarge': 4,
    'm3.2xlarge': 4,
    'm4.large': 2,
    'm4.xlarge': 4,
    'm4.2xlarge': 4,
    'm4.4xlarge': 8,
    'm4.10xlarge': 8,
    'm4.16xlarge': 8,
    'p2.xlarge': 4,
    'p2.8xlarge': 8,
    'p2.16xlarge': 8,
    'r3.large': 3,
    'r3.xlarge': 4,
    'r3.2xlarge': 4,
    'r3.4xlarge': 8,
    'r3.8xlarge': 8,
    'r4.large': 3,
    'r4.xlarge': 4,
    'r4.2xlarge': 4,
    'r4.4xlarge': 8,
    'r4.8xlarge': 8,
    'r4.16xlarge': 15,
    't1.micro': 2,
    't2.nano': 2,
    't2.micro': 2,
    't2.small': 2,
    't2.medium': 3,
    't2.large': 3,
    't2.xlarge': 3,
    't2.2xlarge': 3,
    'x1.16xlarge': 8,
    'x1.32xlarge': 8,
}


class AWSProvider(provider_api.ProviderDriver):

    def __init__(self, cfg=None):
        if not cfg:
            from hypernet_agentless.server import config
            self._cfg = config
        else:
            self._cfg = cfg
        self._access_key_id = self._cfg.aws_access_key_id()
        self._secret_access_key = self._cfg.aws_secret_access_key()
        self._region_name = self._cfg.aws_region_name()
        self.session = session.Session(
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name=self._region_name)
        self.ec2 = self.session.client('ec2')
        self.ec2_resource = self.session.resource('ec2')

    def _find_subnets(self, vpc, tag_name, tag_value):
        return vpc.subnets.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])

    def _find_vms(self, tag_name, tag_values):
        states = [AWS_STATUS[k] for k in [
            'pending', 'running', 'shutting-down', 'stopping', 'stopped']]

        return self.ec2_resource.instances.filter(Filters=[
            {
                'Name': 'tag:%s' % tag_name,
                'Values': tag_values
            },
            {
                'Name': 'instance-state-code',
                'Values': states
            }])

    def _find_image_id(self, tag_name, tag_value):
        images = self.ec2_resource.images.filter(Filters=[{
            'Name': 'tag:%s' % tag_name,
            'Values': ['%s' % tag_value]}])
        for img in images:
            return img.id

    def get_sgs(self, tenant_id):
        hs_sg_name = 'hs_sg_%s' % tenant_id
        vm_sg_name = 'vm_sg_%s' % tenant_id
        hs_sg, vm_sg = None, None
        try:
            resp = self.ec2.describe_security_groups(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [self._cfg.aws_vpc()]},
                    {'Name': 'group-name', 'Values': [
                        hs_sg_name, vm_sg_name]}],
            )

            for sg in resp['SecurityGroups']:
                if sg['GroupName'] == hs_sg_name:
                    hs_sg = sg['GroupId']
                if sg['GroupName'] == vm_sg_name:
                    vm_sg = sg['GroupId']
        except exceptions.ClientError:
            hs_sg = self.ec2.create_security_group(
                GroupName=hs_sg_name,
                Description='%s security group' % vm_sg_name,
                VpcId=self._cfg.aws_vpc()
            )['GroupId']
            vm_sg = self.ec2.create_security_group(
                GroupName=vm_sg_name,
                Description='%s security group' % hs_sg_name,
                VpcId=self._cfg.aws_vpc()
            )['GroupId']
            self.ec2.authorize_security_group_ingress(
                GroupId=hs_sg,
                IpPermissions=[{
                    'IpProtocol': '-1',
                    'FromPort': 0,
                    'ToPort': 65535,
                    'UserIdGroupPairs': [{'GroupId': vm_sg}],
                }]
            )
            self.ec2.authorize_security_group_ingress(
                GroupId=vm_sg,
                IpPermissions=[{
                    'IpProtocol': '-1',
                    'FromPort': 0,
                    'ToPort': 65535,
                    'UserIdGroupPairs': [{'GroupId': hs_sg}],
                }]
            )
        return hs_sg, vm_sg

    def get_subnet(self, name, cidr):
        vpc = self.ec2_resource.Vpc(self._cfg.aws_vpc())
        subnets = self._find_subnets(vpc, 'Name', name)
        for subnet in subnets:
            return subnet.id
        subnet = self.ec2.create_subnet(
            VpcId=self._cfg.aws_vpc(),
            CidrBlock=cidr
        )
        subnet_id = subnet['Subnet']['SubnetId']
        self.ec2.create_tags(
            Resources=[subnet_id],
            Tags=[{
                'Key': 'Name',
                'Value': name
            }]
        )
        return subnet_id

    def _aws_instance_to_dict(self, aws_instance):
        LOG.debug('_aws_instance_to_dict %s' % aws_instance)
        name = None
        vms_ips = []
        mgnt_ip = None
        data_ip = None
        for tag in aws_instance.tags:
            if tag['Key'] == 'Name':
                name = tag['Value']
        vms_nets = self.get_vms_subnet()
        hs_net = self.get_hs_subnet()
        LOG.debug('network_interfaces_attribute %s' % (
            aws_instance.network_interfaces_attribute))
        for net_int in aws_instance.network_interfaces_attribute:
            if net_int['SubnetId'] == self._cfg.mgnt_network():
                mgnt_ip = net_int['PrivateIpAddress']
            if net_int['SubnetId'] == self._cfg.data_network():
                data_ip = net_int['PrivateIpAddress']
            if hs_net:
                if hs_net == net_int['SubnetId']:
                    vms_ips.append({
                        'vms_ip': net_int['PrivateIpAddress'],
                        'index': 0
                    })
            else:
                i = 0
                for vms_net in vms_nets:
                    if vms_net == net_int['SubnetId']:
                        vms_ips.append({
                            'vms_ip': net_int['PrivateIpAddress'],
                            'index': i
                        })
                    i = i + 1
        return provider_api.ProviderHyperswitch(
            instance_id=aws_instance.id,
            name=name,
            instance_type=aws_instance.instance_type,
            mgnt_ip=mgnt_ip,
            data_ip=data_ip,
            vms_ips=vms_ips,
        ).dict

    def create_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hyperswitch_id):
        # find the image according to a tag hybrid_cloud_image=hyperswitch
        image_id = self._find_image_id(
            'hybrid_cloud_image', hs_constants.HYPERSWITCH)
        instance_type = self._cfg.hs_flavor_map()[flavor]
        net_interfaces = []
        i = 0
        for net in net_list:
            if i < MAX_NIC[instance_type]:
                net_interfaces.append(
                    {
                        'DeviceIndex': i,
                        'SubnetId': net['name'],
                        'Groups': net['security_group'],
                    }
                )
                i = i + 1
        user_metadata = ''
        if user_data:
            for k, v in user_data.iteritems():
                user_metadata = '%s\n%s=%s' % (user_metadata, k, v)
        # create the instance
        aws_instance = self.ec2_resource.create_instances(
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            UserData=user_metadata,
            InstanceType=instance_type,
            InstanceInitiatedShutdownBehavior='stop',
            NetworkInterfaces=net_interfaces,
        )[0]

        tags = [{'Key': 'hybrid_cloud_type',
                 'Value': hs_constants.HYPERSWITCH},
                {'Key': 'Name',
                 'Value': hyperswitch_id}]
        self.ec2.create_tags(Resources=[aws_instance.id],
                             Tags=tags)

        aws_instance.wait_until_running()
        aws_instance.reload()
        return self._aws_instance_to_dict(aws_instance)

    def get_hyperswitch(self, hyperswitch_id):
        LOG.debug('get hyperswitch for %s.' % hyperswitch_id)
        i = 0
        aws_instances = self._find_vms('Name', [hyperswitch_id])
        res = None
        for aws_instance in aws_instances:
            if i != 0:
                raise hyperswitch.HyperswitchProviderMultipleFound(
                    hyperswitch_id=hyperswitch_id)
            res = self._aws_instance_to_dict(aws_instance)
        LOG.debug('found hyperswitch for %s = %s.' % (
            hyperswitch_id, res))
        return res

    def start_hyperswitch(self, hyperswitch_id):
        LOG.debug('start hyperswitch %s.' % hyperswitch_id)
        aws_instances = self._find_vms('Name', [hyperswitch_id])
        for aws_instance in aws_instances:
            aws_instance.start()

    def stop_hyperswitch(self, hyperswitch_id):
        LOG.debug('start hyperswitch %s.' % hyperswitch_id)
        aws_instances = self._find_vms('Name', [hyperswitch_id])
        for aws_instance in aws_instances:
            aws_instance.stop()

    def delete_hyperswitch(self, hyperswitch_id):
        LOG.debug('hyperswitch to delete: %s.' % (hyperswitch_id))
        aws_instances = self._find_vms(
            'Name',
            [hyperswitch_id])
        LOG.debug('aws_instances to delete: %s.' % (aws_instances))
        for aws_instance in aws_instances:
            aws_instance.stop()
            aws_instance.wait_until_stopped()
            aws_instance.terminate()
            aws_instance.wait_until_terminated()

    def _network_interface_dict(self, net_int):
        LOG.debug('aws net interface: %s.' % net_int)
        port_id = None
        for tag in net_int['TagSet']:
            if tag['Key'] == 'hybrid_cloud_port_id':
                port_id = tag['Value']
        return provider_api.ProviderPort(
            port_id=port_id,
            provider_ip=net_int['PrivateIpAddress'],
            name=port_id,
        ).dict

    def create_network_interface(self,
                                 port_id,
                                 subnet,
                                 security_group):
        LOG.debug('create net interface (%s, %s, %s).' % (
            port_id, subnet, security_group))
        net_ints = self.ec2.describe_network_interfaces(
            Filters=[{
                'Name': 'tag:hybrid_cloud_port_id',
                'Values': [port_id]
            }]
        )
        net_int = None
        for net_int in net_ints['NetworkInterfaces']:
            pass
        if not net_int:
            net_int = self.ec2.create_network_interface(
                SubnetId=subnet,
                Groups=[security_group]
            )['NetworkInterface']
            resp = None
            while not resp or not resp['NetworkInterfaces']:
                resp = self.ec2.describe_network_interfaces(
                    NetworkInterfaceIds=[net_int['NetworkInterfaceId']])
                time.sleep(1)

        LOG.debug('aws net interface: %s.' % (net_int))
        int_id = net_int['NetworkInterfaceId']
        tags = [{
                    'Key': 'hybrid_cloud_port_id',
                    'Value': port_id
                },
                {
                    'Key': 'hybrid_cloud_type',
                    'Value': 'hybrid_provider_port'
                }]

        self.ec2.create_tags(Resources=[int_id], Tags=tags)

        resp = self.ec2.describe_network_interfaces(
            NetworkInterfaceIds=[int_id])
        for net_int in resp['NetworkInterfaces']:
            return self._network_interface_dict(net_int)

    def delete_network_interface(self, port_id):
        LOG.debug('delete net interface %s.' % port_id)
        resp = self.ec2.describe_network_interfaces(
            Filters=[{
                'Name': 'tag:hybrid_cloud_port_id',
                'Values': [port_id]}]
        )
        for net_int in resp['NetworkInterfaces']:
            self.ec2.delete_network_interface(
                NetworkInterfaceId=net_int['NetworkInterfaceId'])

    def get_network_interface(self, port_id):
        LOG.debug('get net interface %s.' % port_id)
        resp = self.ec2.describe_network_interfaces(
            Filters=[{
                'Name': 'tag:hybrid_cloud_port_id',
                'Values': [port_id]}]
        )
        i = 0
        res = None
        for net_int in resp['NetworkInterfaces']:
            if i != 0:
                raise hyperswitch.ProviderPortProviderPortMultipleFound(
                    providerport_id=port_id)
            res = self._network_interface_dict(net_int)
        LOG.debug('found net interface for %s = %s.' % (port_id, res))
        return res