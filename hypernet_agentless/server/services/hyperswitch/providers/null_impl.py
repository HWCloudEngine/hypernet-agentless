
from hypernet_agentless.server.services.hyperswitch import provider_api

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class NULLProvider(provider_api.ProviderDriver):

    def __init__(self, cfg=None):
        if not cfg:
            from hypernet_agentless.server import config
            self._cfg = config
        else:
            self._cfg = cfg

    def get_sgs(self, tenant_id):
        hs_sg_name = 'hs_sg_%s' % tenant_id
        vm_sg_name = 'vm_sg_%s' % tenant_id
        return hs_sg_name, vm_sg_name

    def get_subnet(self, name, cidr):
        return name

    def create_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hyperswitch_id):
        return {}

    def get_hyperswitch(self, hyperswitch_id):
        return None

    def start_hyperswitch(self, hyperswitch_id):
        pass

    def stop_hyperswitch(self, hyperswitch_id):
        pass

    def delete_hyperswitch(self, hyperswitch_id):
        pass

    def create_network_interface(self,
                                 port_id,
                                 subnet,
                                 security_group):
        return {}

    def delete_network_interface(self, port_id):
        pass

    def get_network_interface(self, port_id):
        return None