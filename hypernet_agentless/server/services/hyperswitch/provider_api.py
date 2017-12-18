import abc


class ProviderDriver(object):

    @abc.abstractmethod
    def get_sgs(self, tenant_id):
        return {'hs_sg': None, 'vm_sg': None}

    @abc.abstractmethod
    def delete_sgs(self, tenant_id):
        return None

    @abc.abstractmethod
    def get_subnet(self, name, cidr):
        return None

    @abc.abstractmethod
    def delete_subnet(self, subnet_id):
        return None

    @abc.abstractmethod
    def create_hyperswitch(self,
                           user_data,
                           flavor,
                           net_list,
                           hyperswitch_id):
        return {}

    @abc.abstractmethod
    def get_hyperswitchs(self, hyperswitch_ids):
        return []

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

    @abc.abstractmethod
    def num_active_network_interface(self, subnet):
        return 0

    @abc.abstractmethod
    def associate_eip(self, hyperswitch_id, eip):
        pass

    @abc.abstractmethod
    def disassociate_eip(self, hyperswitch_id):
        return None

    @abc.abstractmethod
    def allocate_eip(self):
        return None

    @abc.abstractmethod
    def release_eip(self, allocation_id):
        pass

    @abc.abstractmethod
    def get_eip(self, hyperswitch_id):
        return None


class ProviderPort(object):

    def __init__(self, port_id, provider_ip, name, eip_associate):
        self._vals = {
            'id': port_id,
            'provider_ip': provider_ip,
            'name': name,
            'eip_associate': eip_associate,
        }

    @property
    def dict(self):
        return self._vals


class ProviderHyperswitch(object):

    def __init__(self, instance_id, name, instance_type,
                 mgnt_ip, data_ip, fip_ip, vms_ips, id, state, eip):
        self._vals = {
            'instance_id': instance_id,
            'name': name,
            'instance_type': instance_type,
            'mgnt_ip': mgnt_ip,
            'data_ip': data_ip,
            'fip_ip': fip_ip,
            'vms_ips': vms_ips,
            'id': id,
            'state': state,
            'eip': eip,
        }

    @property
    def dict(self):
        return self._vals
