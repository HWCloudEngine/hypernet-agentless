import abc
import six


@six.add_metaclass(abc.ABCMeta)
class VPNDriver(object):

    def __init__(self, index, openvpn_port, first_port):
        self.provider_ips = dict()
        self.index = index
        self.openvpn_port = openvpn_port
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
            del self.provider_ips[provider_ip]
            return port
        return False

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

