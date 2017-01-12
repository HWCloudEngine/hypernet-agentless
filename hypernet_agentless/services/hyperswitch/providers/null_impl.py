
from neutron import manager

from hypernet_agentless.services.hyperswitch import config
from hypernet_agentless.services.hyperswitch import provider_api

from keystoneclient import client

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class NULLProvider(provider_api.ProviderDriver):
    
    def __init__(self):
        # TODO: add fictive tenant, network and subnets according to vms_cidr
        self._plugin_property = None

    @property
    def _plugin(self):
        if self._plugin_property is None:
            self._plugin_property = manager.NeutronManager.get_plugin()
        return self._plugin_property

    def get_sgs(self):
        return config.get_hs_sg_name(), config.get_vm_sg_name()

    def get_vms_subnet(self):
        if config.get_vms_networks():
            return config.get_vms_networks()
        return config.get_vms_cidr()

    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_device_id=None,
                                  hybrid_cloud_tenant_id=None):
        if hybrid_cloud_device_id:
            host = 'vm-%s' % hybrid_cloud_device_id
        else:
            host = 'tenant-%s' % hybrid_cloud_tenant_id
        return host


    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_device_id=None,
                           hybrid_cloud_tenant_id=None):
        LOG.debug('launch hyperswitch %s, %s, %s, %s, %s' % (
            user_data, flavor, net_list,
            hybrid_cloud_device_id, hybrid_cloud_tenant_id))
        return {}

    def get_hyperswitchs(self,
                         names=None,
                         hyperswitch_ids=None,
                         device_ids=None,
                         tenant_ids=None):
        LOG.debug('get hyperswitch for (%s, %s, %s, %s).' % (
            names, hyperswitch_ids, device_ids, tenant_ids))
        return []

    def start_hyperswitchs(self, hyperswitchs):
        LOG.debug('start hyperswitchs %s.' % hyperswitchs)
       
    def delete_hyperswitch(self, hyperswitch_id):
        LOG.debug('hyperswitch to delete: %s.' % (hyperswitch_id))

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
        return {
            'ip': 'xxx.xxx.xxx.xxx',
            'port_id': port_id,
            'device_id': device_id,
            'tenant_id': tenant_id,
            'index': index
        }

    def delete_network_interface(
            self, port_id):
        pass

    def get_network_interfaces(self,
                               context,
                               names=None,
                               port_ids=None,
                               device_ids=None,
                               private_ips=None,
                               tenant_ids=None,
                               indexes=None):
        res = []
        if private_ips:
            for provider_ip in private_ips:
                # TODO: search according to the fictives created subnets
                p_ports = self._plugin.get_ports(context, filters={
                    'fixed_ips': {
                        'ip_address': [provider_ip]
                    }})
                LOG.debug('provider port %s' % p_ports)
                if len(p_ports) != 1:
                    LOG.warn('%d ports for %s' % (len(p_ports), provider_ip))
                    return None
        
                ports = self._plugin.get_ports(context, filters={
                    'id': [p_ports[0]['name']]
                })
                LOG.debug('hyper port %s' % ports)
                if len(ports) != 1:
                    return None
                port = ports[0]
                res.append({
                   'ip': provider_ip,
                   'port_id': port['id'],
                   'device_id': port['device_id'],
                   'tenant_id': port['tenant_id'],
                   'index': 0
                })
        return res
