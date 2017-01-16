from hypernet_agentless.services.hyperswitch.providers import fs_impl
from hypernet_agentless.test.services.hyperswitch.providers import provider_impl


class TestFSProvider(provider_impl.TestProvider):

    @property
    def _provider(self):
        return fs_impl.FSProvider(FSStaticConfig())


class FSStaticConfig(object):
    
    def get_mgnt_network(self):
        return 'private'

    def get_mgnt_security_group(self):
        return 'default'

    def get_data_network(self):
        return '3bd592c8-736b-42bb-93ce-d78e72988e78'

    def get_data_security_group(self):
        return 'default'

    def get_vms_cidr(self):
        return ['172.20.10.0/24']

    def get_hs_sg_name(self):
        return 'hyperswitches_security_group'

    def get_vm_sg_name(self):
        return 'vms_security_group'

    def get_hs_flavor_map(self):
        return {'0G': 'hs.0G',
                '1G': 'hs.1G',
                '10G': 'hs.10G'}

    def get_fs_username(self):
        return 'vpn'

    def get_fs_password(self):
        return 'vpn'

    def get_fs_tenant_id(self):
        return 'b39a38911c934538afefb94594a1b73d'

    def get_fs_auth_url(self):
        return 'http://10.10.10.88:35357/v2.0/'

    def get_fs_availability_zone(self):
        return 'nova'
