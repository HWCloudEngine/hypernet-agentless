import abc
import six
import socket

from hypernet_agentless.agent.hyperswitch.vpn_driver import VPNDriver 
from hypernet_agentless.agent.hyperswitch import hyperswitch_utils as hu

from ryu.ofproto import ether
from ryu.ofproto import inet


class L2tpTUN(VPNDriver):

    def __init__(self, index, vpn_tnl_id, first_port=None):
        self.provider_ips = dict()
        self.index = index
        self.server_ip= vpn_tnl_id 
        

    def add(self, provider_ip, local_ip):
        if provider_ip in self.provider_ips:
            return False
        self.provider_ips[provider_ip].
        pass
    
    def remove(self, provider_ip):
        pass

    def check_port_free(self, local_ip, port):
        return True

    def to_controller_match(self, parser):
        pass

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    def start_vpn(self, tap, br, vpn_nic_ip, mac):
        pass

    def stop_vpn(self, tap):
        pass

