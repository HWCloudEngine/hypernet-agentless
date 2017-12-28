import abc
import six
import socket

from oslo_log import log as logging

from hypernet_agentless.agent.hyperswitch.vpn_driver import VPNDriver
from hypernet_agentless.agent.hyperswitch import hyperswitch_utils as hu

from ryu.ofproto import ether
from ryu.ofproto import inet

LOG = logging.getLogger(__name__)


class OpenVPNTUN(VPNDriver):
    """Implementation OpenVPN related code"""

    def __init__(self, index, vpn_tnl_id, first_port):
        self.provider_ips = dict()
        self.index = index
        self.openvpn_port = vpn_tnl_id
        self.cur_port = first_port
        self.first_port = first_port

    def add(self, provider_ip, local_ip):
        if provider_ip in self.provider_ips:
            return False
        port_free = False
        while not port_free:
            self.cur_port = self.cur_port + 1
            if self.cur_port == 65535:
                self.cur_port = self.first_port
            port_free = self.check_port_free(local_ip, self.cur_port)
        self.provider_ips[provider_ip] = self.cur_port
        return self.cur_port

    def remove(self, provider_ip):
        if provider_ip in self.provider_ips:
            port = self.provider_ips[provider_ip]
            del self.er_ips[provider_ip]
            return port
        return False


class OpenVPNTCP(OpenVPNTUN):

    def __init__(self, index, vpn_tnl_id, first_port):
        super(OpenVPNTCP, self).__init__(
            index=index,
            vpn_tnl_id=vpn_tnl_id,
            first_port=first_port)
        self.proto = 'tcp'
        self.socket_type = socket.SOCK_STREAM
        LOG.debug('OvpnTUN: init driver(%d)', self.index)

    def check_port_free(self, local_ip, port):
        try:
            sock = socket.socket(socket.AF_INET,self.socket_type)
            result = sock.connect_ex((local_ip, port))
            if result == 0:
                return False
            return True
        finally:
            sock.close()

    def to_controller_match(self, parser):
        LOG.debug('OvpnTUN: match for driver(%d)', self.index)
        return parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                               ip_proto=inet.IPPROTO_TCP,
                               tcp_dst=self.openvpn_port)

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        LOG.debug('OvpnTUN: intercept for driver(%d)', self.index)
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_TCP,
                                tcp_dst=self.openvpn_port,
                                ipv4_src=provider_ip),
                [parser.OFPActionSetField(tcp_dst=self.cur_port),
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        LOG.debug('OvpnTUN: return vpn for driver(%d)', self.index)
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_TCP,
                                ipv4_dst=provider_ip,
                                tcp_src=self.cur_port),
                [parser.OFPActionSetField(tcp_src=self.openvpn_port),
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def start_vpn(self, tap, br, vpn_nic_ip, br_nic):
        LOG.debug('OvpnTUN: start vpn for driver(%d)', self.index)
        if hu.device_exists(tap):
            hu.delete_net_dev(tap)

        hu.execute('openvpn', '--mktun', '--dev', tap,
                   check_exit_code=False,
                   run_as_root=True)
        hu.set_device_mtu(tap)

        hu.execute('ip', 'link', 'set', 'dev', tap, 'up',
                   run_as_root=True)
        hu.execute('brctl', 'addif', br, tap,
                   check_exit_code=False,
                   run_as_root=True)

        pid = hu.process_exist(['openvpn', tap])
        if pid:
            hu.execute('kill', str(pid), run_as_root=True)

        hu.launch('openvpn',
                  '--local', vpn_nic_ip,
                  '--port', str(self.cur_port),
                  '--proto', self.proto,
                  '--dev', tap,
                  '--ca', '/etc/openvpn/ca.crt',
                  '--cert', '/etc/openvpn/server.crt',
                  '--key', '/etc/openvpn/server.key',
                  '--dh', '/etc/openvpn/dh2048.pem',
                  '--server-bridge',
                  '--keepalive', '10', '120',
                  '--auth', 'none',
                  '--cipher', 'none',
                  '--status', '/var/log/openvpn-status-%s.log' % tap,
                  '--verb', '4',
                  run_as_root=True)

    def stop_vpn(self, tap):
        LOG.debug('OvpnTUN: stop vpn for driver(%d)', self.index)
        pid = hu.process_exist(['openvpn', tap])
        if pid:
            hu.execute('kill', str(pid), run_as_root=True)
        hu.delete_net_dev(tap)


class OpenVPNUDP(OpenVPNTCP):

    def __init__(self, index, vpn_tnl_id, first_port):
        super(OpenVPNTCP, self).__init__(
            index=index,
            vpn_tnl_id=vpn_tnl_id,
            first_port=first_port)
        self.proto = 'udp'
        self.socket_type = socket.SOCK_DGRAM

    def to_controller_match(self, parser):
        return parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                               ip_proto=inet.IPPROTO_UDP,
                               udp_dst=self.openvpn_port)

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                udp_dst=self.openvpn_port,
                                ipv4_src=provider_ip),
                [parser.OFPActionSetField(udp_dst=self.cur_port),
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_dst=provider_ip,
                                udp_src=self.cur_port),
                [parser.OFPActionSetField(udp_src=self.openvpn_port),
                 parser.OFPActionOutput(ofproto.OFPP_NORMAL)])
