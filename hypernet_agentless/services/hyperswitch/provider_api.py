import abc


class ProviderDriver(object):

    @abc.abstractmethod
    def get_sgs(self):
        return None, None

    @abc.abstractmethod
    def get_vms_subnet(self):
        return []

    @abc.abstractmethod
    def create_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hyperswitch_id):
        return {}

    @abc.abstractmethod
    def get_hyperswitch(self, hyperswitch_id):
        return None

    @abc.abstractmethod
    def start_hyperswitch(self, hyperswitch_id):
        pass

    @abc.abstractmethod
    def stop_hyperswitch(self, hyperswitch_id):
        pass

    @abc.abstractmethod
    def delete_hyperswitch(self, hyperswitch_id):
        pass

    @abc.abstractmethod
    def create_network_interface(self,
                                 port_id,
                                 subnet,
                                 security_group):
        return {}

    @abc.abstractmethod
    def delete_network_interface(self, port_id):
        pass

    @abc.abstractmethod
    def get_network_interface(self, port_id):
        return None