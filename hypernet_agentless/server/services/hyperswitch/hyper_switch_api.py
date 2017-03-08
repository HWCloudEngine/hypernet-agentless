from keystoneauth1 import loading

from hypernet_agentless.common import hs_constants
from hypernet_agentless.server import config, manager

from neutronclient.v2_0 import client as neutron_client

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging


LOG = logging.getLogger(__name__)


class HyperswitchCallback(object):
    """
        Processes the rpc call back.
    """

    RPC_API_VERSION = '1.0'

    def __init__(self):
        endpoints = [self]
        transport = oslo_messaging.get_transport(cfg.CONF)
        target = oslo_messaging.Target(
            topic=hs_constants.HYPERSWITCH_CALLBACK,
            version='1.0',
            exchange=hs_constants.HYPERSWITCH,
            server=config.host())
        self.server = oslo_messaging.get_rpc_server(
            transport, target, endpoints)
        self.server.start()
        self._neutron_client_property = None
        self._hyperswitch_plugin_property = None
        super(HyperswitchCallback, self).__init__()

    @property
    def _neutron_client(self):
        if self._neutron_client_property is None:
            auth_plugin = loading.load_auth_from_conf_options(
                cfg.CONF, 'neutron')
            auth_session = loading.load_session_from_conf_options(
                cfg.CONF, 'neutron')
            self._neutron_client_property = neutron_client.Client(
                session=auth_session,
                auth=auth_plugin,
                endpoint_override=cfg.CONF.neutron.url,
                region_name=cfg.CONF.neutron.region_name)
        return self._neutron_client_property

    @property
    def _hyperswitch_plugin(self):
        if self._hyperswitch_plugin_property is None:
            self._hyperswitch_plugin_property = (
                manager.HypernetManager.get_service_plugins().get(
                    hs_constants.HYPERSWITCH))
        return self._hyperswitch_plugin_property

    def get_vif_for_provider_ip(self, context, **kwargs):
        """
            Return a port data from a provider IP.
        """
        provider_ip = kwargs['provider_ip']
        host_id = kwargs['host_id']
        evt = kwargs['evt']
        LOG.debug('get_vif_for_provider_ip %s' % provider_ip)
        
        p_ports = self._hyperswitch_plugin.get_providerports(
            context, filters={'provider_ip': [provider_ip]})
        LOG.debug('provider ports for %s: %s' % (
            provider_ip, p_ports))
        if len(p_ports) != 1:
            LOG.warn('%d ports for %s' % (len(p_ports), provider_ip))
            return None

        ports = self._neutron_client.list_ports(
            id=[p_ports[0]['id']])
        LOG.debug('hyper port %s' % ports)
        if len(ports) != 1:
            return None
        port = ports[0]
        if evt == 'up':
            self._neutron_client.update_port(
                port['id'],
                {'port': {'binding:host_id': host_id}})
            tenant_id = port['tenant_id']
            LOG.debug('tenant_id: %s' % tenant_id)
            routers = self._neutron_client.list_routers(
                tenant_id=[tenant_id])
            LOG.debug('routers: %s' % routers)
            for router in routers:
                self._neutron_client.update_router(
                    router['id'],
                    {'router': {'admin_state_up': False}})
                self._neutron_client.update_router(
                    router['id'],
                    {'router': {'admin_state_up': True}})

        return {'device_id': port['device_id'],
                'vif_id': port['id'],
                'mac': port['mac_address']}


class HyperswitchAPI(object):
    """
        Client side of the Hyper Switch RPC API
    """

    def __init__(self):
        transport = oslo_messaging.get_transport(cfg.CONF)
        target = oslo_messaging.Target(
            topic=hs_constants.HYPERSWITCH_UPDATE,
            version='1.0',
            exchange=hs_constants.HYPERSWITCH)
        self.client = oslo_messaging.RPCClient(transport, target)
        self.call_back = HyperswitchCallback()
        super(HyperswitchAPI, self).__init__()