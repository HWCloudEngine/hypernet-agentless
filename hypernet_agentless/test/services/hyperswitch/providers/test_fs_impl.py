import unittest

from hypernet_agentless.services.hyperswitch.providers import fs_impl


class TestFSProvider(unittest.TestCase):
    
#     def test_launch_hypeswitch(self):
#         provider = fs_impl.FSProvider(StTinyDbDriveraticConfig())
#         nets = provider.get_vms_subnet()
#         hs_sg, vm_sg = provider.get_sgs()
#         hs = provider.launch_hyperswitch(
#             {'1': '2'},
#             '0G',
#             [{'name': nets[0],
#               'security_group': [vm_sg]}],
#             hybrid_cloud_tenant_id='12345'
#         )
#         print(hs)
#         
#     def test_get_hyperswitchs(self):
#         provider = fs_impl.FSProvider(StaticConfig())
#         hss = provider.get_hyperswitchs(tenant_ids=['12345'])
#         print(hss)
# 
#     def test_start_hyperswitchs(self):
#         provider = fs_impl.FSProvider(StaticConfig())
#         hss = provider.get_hyperswitchs(tenant_ids=['12345'])
#         provider.start_hyperswitchs(hss)
# 
#     def test_delete_hyperswitchs(self):
#         provider = fs_impl.FSProvider(StaticConfig())
#         hss = provider.get_hyperswitchs(tenant_ids=['12345'])
#         for hs in hss:
#             provider.delete_hyperswitch(hs['id'])

    def test_1_create_network_interface(self):
        provider = fs_impl.FSProvider(StaticConfig())
        nets = provider.get_vms_subnet()
        _, vm_sg = provider.get_sgs()
        res = provider.create_network_interface(
            port_id='123456',
            device_id=None,
            tenant_id=None,
            index=0,
            subnet=nets[0],
            security_group=vm_sg)
        self.assertEqual('123456',res['port_id'])
        TestFSProvider.ip = res['ip']

    def test_2_get_network_interfaces(self):
        provider = fs_impl.FSProvider(StaticConfig())
        res = provider.get_network_interfaces(names=['123456'])
        self.assertEqual(1, len(res))
        self.assertEqual('123456',res[0]['port_id'])
        if hasattr(TestFSProvider, 'ip'):
            self.assertEqual(TestFSProvider.ip, res[0]['ip'])
        res = provider.get_network_interfaces(port_ids=['123456'])
        self.assertEqual(1, len(res))
        self.assertEqual('123456',res[0]['port_id'])
        if hasattr(TestFSProvider, 'ip'):
            self.assertEqual(TestFSProvider.ip, res[0]['ip'])

    def test_3_delete_network_interface(self):
        provider = fs_impl.FSProvider(StaticConfig())
        res = provider.delete_network_interface(port_id='123456')
        self.assertTrue(res)
 

class StaticConfig(object):
    
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
