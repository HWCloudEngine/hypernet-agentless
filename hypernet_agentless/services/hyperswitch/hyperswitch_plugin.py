
from hypernet_agentless.services.hyperswitch import config
from hypernet_agentless.services.hyperswitch import hyper_switch_api
from hypernet_agentless.services.hyperswitch.providers import aws_impl
from hypernet_agentless.services.hyperswitch.providers import null_impl
from hypernet_agentless.extensions import hyperswitch

from neutron import manager

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class HyperswitchPlugin(hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = ["hyperswitch"]
    
    def __init__(self):
        if config.get_provider() == 'aws':
            self._provider_impl = aws_impl.AWSProvider()
        elif config.get_provider() == 'openstack':
            self._provider_impl = aws_impl.AWSProvider()
        else:
            self._provider_impl = null_impl.NULLProvider()
        self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
        self._vms_subnets = self._provider_impl.get_vms_subnet()
        self._hs_sg, self._vm_sg  = self._provider_impl.get_sgs()

    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def get_plugin_type(self):
        """Get type of the plugin."""
        return "hyperswitch"

    def get_plugin_description(self):
        """Get description of the plugin."""
        return "Hyperswitch Management Plugin"

    def _make_agentlessport_dict(self, port, net_int, hsservers):
        LOG.debug('_make_agentlessport_dict %s, %s, %s' % (
            port, net_int, hsservers))
        hsservers_ip = None
        index = net_int['index']
        for hsserver in hsservers:
            if hsservers_ip:
                hsservers_ip = '%s, %s' % (
                    hsservers_ip, hsserver['vms_ip_%d' % index])
            else:
                hsservers_ip = '%s' % hsserver['vms_ip_%d' % index]
        res = {
            'id': port['id'],
            'index': index,
            'tenant_id': port['tenant_id'],
            'user_data': 'mac%d = %s\nhsservers%d = %s' % (
                index, port['mac_address'], index, hsservers_ip)
        }
        if 'device_id' in net_int:
            res['device_id'] = net_int['device_id']
        if 'flavor' in net_int:
            res['flavor'] = net_int['flavor']
        return res

    def create_agentlessport(self, context, agentlessport):
        #   - create a provider port with the name port_id
        port = agentlessport['agentlessport']
        port_id = port.get('port_id')
        ports = self._core_plugin.get_ports(
            context,
            filters={'id': [port_id]})
        if not ports:
            LOG.error('No Neutron port found for %s.' % (port_id))
            return None
        if len(ports) != 1:
            LOG.error('%d Neutron ports found for %s.' % (
                len(ports), port_id))
            return None
        neutron_port = ports[0]
        index = port.get('index')
        ag_device_id = agentlessport.get('device_id')
        device_id = neutron_port['device_id']
        if ag_device_id and ag_device_id != device_id:
            LOG.error('No device id match (received: %s, neutron: %s).' % (
                ag_device_id, device_id))
            return None
        tenant_id = neutron_port['tenant_id']
        flavor = port.get('flavor')
        if not flavor:
            flavor = config.get_default_flavor()
        net_int = self._provider_impl.create_network_interface(
            port_id,
            device_id,
            tenant_id,
            index,
            self._vms_subnets[index],
            self._vm_sg)
        #   - retrieve the list of hyperswitch
        if config.get_level() == 'vm' or ag_device_id:
            hsservers = self._provider_impl.get_hyperswitchs(
                device_ids=[device_id])
            if not hsservers or len(hsservers) == 0:
                hsservers = [self.create_hyperswitch(context, {
                    'hyperswitch': {
                        'device_id': device_id,
                        'flavor': flavor
                    }
                })]
        else:
            hsservers = self._provider_impl.get_hyperswitchs(
                tenant_ids=[tenant_id])
            if not hsservers or len(hsservers) == 0:
                hsservers = [self.create_hyperswitch(context, {
                    'hyperswitch': {
                        'tenant_id': tenant_id,
                        'flavor': flavor
                    }
                })]
        self._provider_impl.start_hyperswitchs(hsservers)
        return self._make_agentlessport_dict(neutron_port, net_int, hsservers)

    def get_agentlessport(self, context, agentlessport_id, fields=None):
        LOG.debug('get agentless port %s.' % agentlessport_id)
        ports = self._core_plugin.get_ports(
            context,
            filters={'id': [agentlessport_id]})
        if not ports:
            LOG.error('No agentless port found for %s.' % (agentlessport_id))
            return None
        if len(ports) != 1:
            LOG.error('%d agentless ports found for %s.' % (
                len(ports), agentlessport_id))
            return None
        net_int = self._provider_impl.get_network_interfaces(
            context, [agentlessport_id])[0]
        hsservers = self._provider_impl.get_hyperswitchs(
            device_ids=[ports[0]['device_id']])
        if not hsservers or len(hsservers) == 0:
            hsservers = self._provider_impl.get_hyperswitchs(
                tenant_ids=[ports[0]['tenant_id']])
        return self._make_agentlessport_dict(ports[0], net_int, hsservers)

    def delete_agentlessport(self, context, agentlessport_id):
        LOG.debug('removing agentless port %s.' % agentlessport_id)
        self._provider_impl.delete_network_interface(agentlessport_id)

    def get_agentlessports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        LOG.debug('get agentless ports %s.' % filters)
        if not filters:
            filters = {}
        net_ints = self._provider_impl.get_network_interfaces(
            context,
            filters.get('name'),
            filters.get('port_id'),
            filters.get('device_id'),
            filters.get('private_ip'),
            filters.get('tenant_id'),
            filters.get('index')
        )
        res = []
        for net_int in net_ints:
            ports = self._core_plugin.get_ports(
                context,
                filters={'id': [net_int['port_id']]})
            if ports and len(ports) > 0:
                hsservers = self._provider_impl.get_hyperswitchs(
                    device_ids=[ports[0]['device_id']])
                if not hsservers or len(hsservers) == 0:
                    hsservers = self._provider_impl.get_hyperswitchs(
                    tenant_ids=[ports[0]['tenant_id']])
                res.append(self._make_agentlessport_dict(
                    ports[0], net_int, hsservers))
        return res

    def create_hyperswitch(self, context, hyperswitch):
        LOG.debug('hyperswitch %s to create.' % hyperswitch)
        hyperswitch = hyperswitch['hyperswitch']
        rabbit_hosts = None
        for rabbit_host in config.get_rabbit_hosts():
            if rabbit_hosts:
                rabbit_hosts = '%s, %s' % (rabbit_hosts, rabbit_host)
            else:
                rabbit_hosts = rabbit_host
        host = self._provider_impl.get_hyperswitch_host_name(
            hyperswitch.get('device_id'),
            hyperswitch.get('tenant_id'))
        user_data = {
            'rabbit_userid': config.get_rabbit_userid(),
            'rabbit_password': config.get_rabbit_password(),
            'rabbit_hosts': rabbit_hosts,
            'host': host,
            'network_mngt_interface': 'eth0',
            'network_data_interface': 'eth1',
            'network_vms_interface': 'eth2',
        }

        net_list = [
            {
                'name': config.get_mgnt_network(),
                'security_group': config.get_mgnt_security_group()},
            {
                'name': config.get_data_network(),
                'security_group': config.get_data_security_group()},
        ]
        # TODO: use security groups for HSs and VMs
        for vm_subnet in self._vms_subnets:
            net_list.append(
                {
                    'name': vm_subnet,
                    'security_group': self._hs_sg
                }
            )
        hs = self._provider_impl.launch_hyperswitch(
            user_data,
            hyperswitch['flavor'],
            net_list,
            hyperswitch.get('device_id'),
            hyperswitch.get('tenant_id'),
        )
        LOG.debug('hyperswitch %s created.' % hs)
        return hs

    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        LOG.debug('hyperswitch %s to show.' % hyperswitch_id)
        hs = self._provider_impl.get_hyperswitchs(
            [hyperswitch_id]
        )
        LOG.debug('%d hyperswitch found for %s: %s.' % (
            len(hs), hyperswitch_id, hs))
        if len(hs) > 0:
            return hs[0]
        else:
            return None

    def delete_hyperswitch(self, context, hyperswitch_id):
        LOG.debug('hyperswitch %s to delete.' % hyperswitch_id)
        self._provider_impl.delete_hyperswitch(hyperswitch_id)
        agents = self._core_plugin.get_agents(
            context,
            filters={'host': [hyperswitch_id]})
        LOG.debug('agents to delete: %s' % agents)
        for agent in agents:
            self._core_plugin.delete_agent(context, agent.get('id'))

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug('get hyperswitch %s.' % filters)
        if not filters:
            filters = {}
        return self._provider_impl.get_hyperswitchs(
            filters.get('name'),
            filters.get('id'),
            filters.get('tenant_id'),
            filters.get('device_id')
        )

