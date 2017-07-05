import unittest


class TestProvider(unittest.TestCase):

    @property
    def _provider(self):
        return None

    def test_1_launch_hyperswitch(self):
        net = self._provider.get_subnet('name', '172.31.120.0/24')
        _, vm_sg = self._provider.get_sgs()
        hs = self._provider.launch_hyperswitch(
            {'1': '2'},
            '0G',
            [{'name': net,
              'security_group': [vm_sg]}],
            hybrid_cloud_tenant_id='12345'
        )
        self.assertEqual('12345', hs['tenant_id'])

    def test_2_start_hyperswitchs(self):
        hss = self._provider.get_hyperswitchs(tenant_ids=['12345'])
        self._provider.start_hyperswitchs(hss)

    def test_3_get_hyperswitchs(self):
        hss = self._provider.get_hyperswitchs(tenant_ids=['12345'])
        self.assertEqual(1, len(hss))
        self.assertEqual('12345', hss[0]['tenant_id'])

    def test_4_delete_hyperswitchs(self):
        hss = self._provider.get_hyperswitchs(tenant_ids=['12345'])
        for hs in hss:
            self._provider.delete_hyperswitch(hs['id'])

    def test_1_create_network_interface(self):
        net = self._provider.get_subnet('name', '172.31.120.0/24')
        _, vm_sg = self._provider.get_sgs()
        res = self._provider.create_network_interface(
            port_id='123456',
            device_id=None,
            tenant_id=None,
            index=0,
            subnet=net,
            security_group=vm_sg)
        self.assertEqual('123456', res['port_id'])
        TestProvider.ip = res['ip']

    def test_2_get_network_interfaces(self):
        res = self._provider.get_network_interfaces(names=['123456'])
        self.assertEqual(1, len(res))
        self.assertEqual('123456', res[0]['port_id'])
        if hasattr(TestProvider, 'ip'):
            self.assertEqual(TestProvider.ip, res[0]['ip'])
        res = self._provider.get_network_interfaces(port_ids=['123456'])
        self.assertEqual(1, len(res))
        self.assertEqual('123456', res[0]['port_id'])
        if hasattr(TestProvider, 'ip'):
            self.assertEqual(TestProvider.ip, res[0]['ip'])

    def test_3_delete_network_interface(self):
        res = self._provider.delete_network_interface(port_id='123456')
        self.assertTrue(res)
