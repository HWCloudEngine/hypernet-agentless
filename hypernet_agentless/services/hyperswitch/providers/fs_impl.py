
from hypernet_agentless.services.hyperswitch import provider_api

from neutronclient.v2_0 import client as neutron_client

from novaclient.v1_1 import client as nova_client

from neutron.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class FSProvider(provider_api.ProviderDriver):
    
    def __init__(self, cfg=None):
        if not cfg:
            from hypernet_agentless.services.hyperswitch import config
            self._cfg = config
        else:
            self._cfg = cfg
        self._neutron_client_property = None
        self._nova_client_property = None
        self._net_ids = {}
        self._vm_nets = []

    @property
    def _neutron_client(self):
        if self._neutron_client_property is None:
            self._neutron_client_property = neutron_client.Client(
                username=self._cfg.get_fs_username(),
                password=self._cfg.get_fs_password(),
                tenant_id=self._cfg.get_fs_tenant_id(),
                auth_url=self._cfg.get_fs_auth_url())
        return self._neutron_client_property

    @property
    def _nova_client(self):
        if self._nova_client_property is None:
            self._nova_client_property = nova_client.Client(
                username=self._cfg.get_fs_username(),
                api_key=self._cfg.get_fs_password(),
                tenant_id=self._cfg.get_fs_tenant_id(),
                auth_url=self._cfg.get_fs_auth_url())
        return self._nova_client_property

    def _get_net_id(self, id_or_name):
        if not id_or_name in self._net_ids:
            try:
                self._net_ids[id_or_name] = (
                    self._neutron_client.show_network(
                        id_or_name)['network']['id']
                )
            except:
                self._net_ids[id_or_name] = (
                    self._neutron_client.list_networks(
                        name=id_or_name)['networks'][0]['id']
                )
        return self._net_ids[id_or_name]

    def _net_equal(self, net1, net2):
        return self._get_net_id(net1) == self._get_net_id(net2) 

    def get_sgs(self):
        hs_sg, vm_sg = None, None
        security_groups = self._neutron_client.list_security_groups(
            name=[self._cfg.get_hs_sg_name(), self._cfg.get_vm_sg_name()]
        )['security_groups']
        if len(security_groups) > 0:
            for sg in security_groups:
                if sg['name'] == self._cfg.get_hs_sg_name():
                    hs_sg = sg['id']
                if sg['name'] == self._cfg.get_vm_sg_name():
                    vm_sg = sg['id']
        else:
            hs_sg = self._neutron_client.create_security_group(
                {'security_group': {
                    'name': self._cfg.get_hs_sg_name(),
                    'description': ('%s security group' %
                                    self._cfg.get_hs_sg_name()),
                    'tenant_id': self._cfg.get_fs_tenant_id()
                }}
            )['security_group']['id']
            vm_sg = self._neutron_client.create_security_group({
                'security_group': {
                    'name': self._cfg.get_vm_sg_name(),
                    'description': ('%s security group' %
                                    self._cfg.get_hs_sg_name()),
                    'tenant_id': self._cfg.get_fs_tenant_id()
                }}
            )['security_group']['id']
            self._neutron_client.create_security_group_rule({
                'security_group_rule': {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'remote_group_id': hs_sg,
                    'security_group_id': vm_sg,
                    'tenant_id': self._cfg.get_fs_tenant_id()
                }}
            )
            self._neutron_client.create_security_group_rule({
                'security_group_rule': {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'remote_group_id': vm_sg,
                    'security_group_id': hs_sg,
                    'tenant_id': self._cfg.get_fs_tenant_id()
                }}
            )
        return hs_sg, vm_sg

    def get_vms_subnet(self):
        if len(self._vm_nets) != len(self._cfg.get_vms_cidr()):
            for cidr in self._cfg.get_vms_cidr():
                snets = self._neutron_client.list_subnets(cidr=cidr)['subnets']
                if len(snets) > 0:
                    self._vm_nets = self._vm_nets + snets
        subnets_id = []
        for net in self._vm_nets:
            subnets_id.append(net['network_id'])
        return subnets_id

    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_device_id=None,
                                  hybrid_cloud_tenant_id=None):
        if hybrid_cloud_device_id:
            host = 'hs####dev####%s' % hybrid_cloud_device_id
        else:
            host = 'hs####tenant####%s' % hybrid_cloud_tenant_id
        return host

    def _find_image(self, key, value):
        images = self._nova_client.images.list()
        for image in images:
            if key in image.metadata and image.metadata[key] == value:
                return image
        return None

    def _find_flavor(self, name):
        for flavor in self._nova_client.flavors.list():
            if flavor.name == name:
                return flavor
        return None

    def _fs_instance_to_dict(self, fs_instance):
        LOG.debug('_fs_instance_to_dict %s' % fs_instance)
        res = {
            'id': fs_instance.id,
            'device_id': fs_instance.metadata.get('hybrid_cloud_device_id'),
            'tenant_id': fs_instance.metadata.get('hybrid_cloud_tenant_id'),
            'instance_id': fs_instance.id,
            'instance_type': self._get_flavor_name(fs_instance.flavor['id']),
        }
        vm_nets = self.get_vms_subnet()
        for net_int in fs_instance.networks:
            if self._net_equal(net_int, self._cfg.get_mgnt_network()):
                res['mgnt_ip'] = fs_instance.networks[net_int][0]
            if self._net_equal(net_int, self._cfg.get_data_network()):
                res['data_ip'] = fs_instance.networks[net_int][0]
            i = 0
            for net in vm_nets:
                if self._net_equal(net_int, net):
                    res['vms_ip_%d' % i] = fs_instance.networks[net_int][0]
                i = i + 1
        if 'mgnt_ip' in res:
            res['private_ip'] = res['mgnt_ip']
        
        return res

    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_device_id=None,
                           hybrid_cloud_tenant_id=None):
        LOG.debug('launch hyperswitch %s, %s, %s, %s, %s' % (
            user_data, flavor, net_list,
            hybrid_cloud_device_id, hybrid_cloud_tenant_id))
        hs_name = self.get_hyperswitch_host_name(
            hybrid_cloud_device_id,
            hybrid_cloud_tenant_id
        )
        hs_img = self._find_image('hybrid_cloud_image', 'hyperswitch')
        hs_flavor = self._find_flavor(self._cfg.get_hs_flavor_map()[flavor])
        user_metadata = ''
        for k, v in user_data.iteritems():
            user_metadata = '%s\n%s=%s' % (user_metadata, k, v)

        nics = []
        for net in net_list:
            port = self._neutron_client.create_port({
                'port': {
                    'security_groups': net['security_group'],
                    'tenant_id': self._cfg.get_fs_tenant_id(),
                    'network_id': net['name']
            }})['port']
            nics.append({'port-id': port['id']})
        
        meta = {
            'hybrid_cloud_tenant_id': hybrid_cloud_tenant_id,
            'hybrid_cloud_type': 'hyperswitch'
        }
        if hybrid_cloud_device_id:
            meta['hybrid_cloud_device_id'] = hybrid_cloud_device_id
        hs_instance = self._nova_client.servers.create(
             hs_name,
             hs_img,
             hs_flavor,
             meta=meta,
             nics=nics,
             userdata=user_metadata,
             availability_zone=self._cfg.get_fs_availability_zone())
        return self._fs_instance_to_dict(hs_instance)

    def _get_hyperswitchs(self, name, res):
        for inst in self._nova_client.servers.list(search_opts={'name': name}):
            res.append(self._fs_instance_to_dict(inst))
        return res

    def _get_flavor_name(self, flavor_id):
        return self._nova_client.flavors.get(flavor_id).name

    def get_hyperswitchs(self,
                         names=None,
                         hyperswitch_ids=None,
                         device_ids=None,
                         tenant_ids=None):
        LOG.debug('get hyperswitch for (%s, %s, %s, %s).' % (
            names, hyperswitch_ids, device_ids, tenant_ids))
        res = []
        has_filter = False
        if names:
            for name in names:
                self._get_hyperswitchs(name, res)
            has_filter = True
        if hyperswitch_ids:
            for hyperswitch_id in hyperswitch_ids:
                self._get_hyperswitchs(hyperswitch_id, res)
            has_filter = True
        if device_ids:
            for device_id in device_ids:
                self._get_hyperswitchs('hs####dev####%s' % device_id, res)
            has_filter = True
        if tenant_ids:
            for tenant_id in tenant_ids:
                self._get_hyperswitchs('hs####tenant####%s' % tenant_id, res)
            has_filter = True
        if not has_filter:
            self._get_hyperswitchs('hs####*', res)
        return res 
            

    def start_hyperswitchs(self, hyperswitchs):
        LOG.debug('start hyperswitchs %s.' % hyperswitchs)
        for hyperswitch in hyperswitchs:
            hs = self._nova_client.servers.get(hyperswitch['id'])
            if not hs.status in ['ACTIVE', 'BUILD']:
                self._nova_client.servers.start(hyperswitch['id'])
       
    def delete_hyperswitch(self, hyperswitch_id):
        LOG.debug('hyperswitch to delete: %s.' % (hyperswitch_id))
        self._nova_client.servers.delete(hyperswitch_id)

    def _to_net_int(self, port):
        return {
               'ip': port['fixed_ips'][0]['ip_address'],
               'port_id': port['name'],
               'device_id': None,
               'tenant_id': None,
               'index': 0
        }
    
    def create_network_interface(
            self,
            port_id,
            device_id,
            tenant_id,
            index,
            subnet,
            security_group):
        LOG.debug('create net interface (%s, %s, %s, %d, %s, %s).' % (
            port_id, device_id, tenant_id, index, subnet, security_group))
        ports = self._neutron_client.list_ports(name=[port_id])['ports']
        if len(ports) == 0 :
            port = self._neutron_client.create_port({'port': {
                'name': port_id,
                'tenant_id': self._cfg.get_fs_tenant_id(),
                'security_groups': [security_group],
                'network_id': subnet
            }})['port']
        else:
            if len(ports) != 1:
                pass #TODO: exception
            port = ports[0]
        LOG.debug('port: %s.' % (port))
        return self._to_net_int(port)

    def delete_network_interface(
            self, port_id):
        LOG.debug('delete net interface (%s).' % (port_id))
        ports = self._neutron_client.list_ports(name=[port_id])['ports']
        if len(ports) == 0:
            return False
        for port in ports:
            self._neutron_client.delete_port(port['id'])
        return True

    def _add_net_int(self, ports_res, res):
        for port in ports_res['ports']:
            res.append(self._to_net_int(port))

    def get_network_interfaces(self,
                               context=None,
                               names=None,
                               port_ids=None,
                               device_ids=None,
                               private_ips=None,
                               tenant_ids=None,
                               indexes=None):
        res = []
        has_filter = False
        if names:
            self._add_net_int(
                self._neutron_client.list_ports(name=names), res)
            has_filter = True
        if port_ids:
            self._add_net_int(
                self._neutron_client.list_ports(name=port_ids), res)
            has_filter = True
        if device_ids:
            pass #TODO: exception
        if private_ips:
            self._add_net_int(
                self._neutron_client.list_ports(fixed_ips={
                    'ip_address': private_ips}), res)
            has_filter = True
        if indexes:
            pass #TODO: exception
        if not has_filter:
            pass #TODO: exception
        return res
