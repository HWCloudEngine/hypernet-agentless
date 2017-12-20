import abc
import six


@six.add_metaclass(abc.ABCMeta)
class VPNDriver(object):

    @abc.abstractmethod
    def __init__(self, index, vpn_tnl_id, first_port=None):
        pass

    @abc.abstractmethod
    def add(self, provider_ip, local_ip):
        pass

    @abc.abstractmethod
    def remove(self, provider_ip):
        pass

    @abc.abstractmethod
    def check_port_free(self, local_ip, port):
        return True

    @abc.abstractmethod
    def to_controller_match(self, parser):
        pass

    @abc.abstractmethod
    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    @abc.abstractmethod
    def return_vpn_packets(self, parser, ofproto, provider_ip):
        pass

    @abc.abstractmethod
    def start_vpn(self, tap, br, vpn_nic_ip, mac):
        pass

    @abc.abstractmethod
    def stop_vpn(self, tap):
        pass

