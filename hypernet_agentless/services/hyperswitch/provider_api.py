import abc


class ProviderDriver(object):

    @abc.abstractmethod
    def get_sgs(self):
        return None, None

    @abc.abstractmethod
    def get_vms_subnet(self):
        return []

    @abc.abstractmethod
    def get_hyperswitch_host_name(self,
                                  hybrid_cloud_device_id=None,
                                  hybrid_cloud_tenant_id=None):
        pass

    @abc.abstractmethod
    def launch_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hybrid_cloud_device_id=None,
                           hybrid_cloud_tenant_id=None):
        pass

    @abc.abstractmethod
    def get_hyperswitchs(self,
                         names=None,
                         hyperswitch_ids=None,
                         device_ids=None,
                         tenant_ids=None):
        return []

    @abc.abstractmethod
    def start_hyperswitchs(self, hyperswitchs):
        pass

    @abc.abstractmethod
    def delete_hyperswitch(self, hyperswitch_id):
        pass

    @abc.abstractmethod
    def create_network_interface(
            self,
            port_id,
            device_id,
            tenant_id,
            index,
            subnet,
            security_group):
        pass

    # Only get by name and private_ips is necessary to implement,
    # the other one are optionals
    @abc.abstractmethod
    def get_network_interfaces(self,
                               context,
                               names=None,
                               port_ids=None,
                               device_ids=None,
                               private_ips=None,
                               tenant_ids=None,
                               indexes=None):
        pass