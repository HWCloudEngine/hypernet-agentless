
from hypernet_agentless.services.hyperswitch.providers import fs_impl
from hypernet_agentless.test.services.hyperswitch import providers


class TestFSProvider(providers.provider_impl.TestProvider):

    @property
    def _provider(self):
        return fs_impl.FSProvider(FSStaticConfig())


class FSStaticConfig(object):

    def mgnt_network(self):
        return 'private'

    def mgnt_security_group(self):
        return 'default'

    def data_network(self):
        return '3bd592c8-736b-42bb-93ce-d78e72988e78'

    def data_security_group(self):
        return 'default'

    def hs_flavor_map(self):
        return {'0G': 'hs.0G',
                '1G': 'hs.1G',
                '10G': 'hs.10G'}

    def fs_username(self):
        return 'vpn'

    def fs_password(self):
        return 'vpn'

    def fs_tenant_id(self):
        return 'b39a38911c934538afefb94594a1b73d'

    def fs_auth_url(self):
        return 'http://10.10.10.88:35357/v2.0/'

    def fs_availability_zone(self):
        return 'nova'
