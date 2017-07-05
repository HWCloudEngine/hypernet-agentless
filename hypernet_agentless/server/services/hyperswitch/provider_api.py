import abc


class ProviderDriver(object):

    @abc.abstractmethod
    def get_sgs(self, tenant_id):
        return None, None

    @abc.abstractmethod
    def get_subnet(self, name, cidr):
        return None

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


class ProviderPort(object):

    def __init__(self, port_id, provider_ip, name):
        self._vals = {
            'id': port_id,
            'provider_ip': provider_ip,
            'name': name,
        }

    @property
    def dict(self):
        return self._vals


class ProviderHyperswitch(object):

    def __init__(self, instance_id, name, instance_type,
                 mgnt_ip, data_ip, vms_ips):
        self._vals = {
            'instance_id': instance_id,
            'name': name,
            'instance_type': instance_type,
            'mgnt_ip': mgnt_ip,
            'data_ip': data_ip,
            'vms_ips': vms_ips,
        }

    @property
    def dict(self):
        return self._vals
