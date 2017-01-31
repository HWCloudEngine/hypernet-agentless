
from neutron import manager

from hypernet_agentless.services.hyperswitch import provider_api

from neutron.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class NULLProvider(provider_api.ProviderDriver):
    
    def __init__(self, cfg=None):
        if not cfg:
            from hypernet_agentless.services.hyperswitch import config
            self._cfg = config
        else:
            self._cfg = cfg

    def get_sgs(self):
        return self._cfg.get_hs_sg_name(), self._cfg.get_vm_sg_name()

    def get_vms_subnet(self):
        if self._cfg.get_vms_networks():
            return self._cfg.get_vms_networks()
        return self._cfg.get_vms_cidr()

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