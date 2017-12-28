import abc
import six
import socket

from oslo_log import log as logging

from hypernet_agentless.agent.hyperswitch.vpn_driver import VPNDriver
from hypernet_agentless.agent.hyperswitch import hyperswitch_utils as hu

from ryu.ofproto import ether
from ryu.ofproto import inet

LOG = logging.getLogger(__name__)

## Templates for xl2tpd configuration files
xl2tpd_conf = [
    '[global]','access control = yes','auth file = %s','debug avp =no','debug network = no',
    'debug packet = no', 'debug state = no','debug tunnel = yes','[lns default]',
    'require chap = yes','ppp debug = yes', 'pppoptfile = %s','require pap = yes',
    'assign ip = yes','hostname = %s','ip range = %s', 'local ip = %s','challenge = no',
    'lac = %s','require authentication = yes']
options_l2tpd = [
    'ipcp-accept-local','ipcp-accept-remote','mtu 1410','mru 1410','ms-dns 8.8.8.8',
    'require-mschap-v2','asyncmap 0','auth','crtscts','lock','hide-password',
    'modem','debug','name username','proxyarp','lcp-echo-interval 10',
    'lcp-echo-failure 100','connect-delay 5000']
chap_secret = "%s * %s *"
l2tp_secret = "* * %s"


class L2tpTUN(VPNDriver):

    def __init__(self, index, vpn_tnl_id, first_port=None):
        self.provider_ips = dict()
        self.index = index
        self.server_ip= vpn_tnl_id
        self.server_port=1701
        self.server_running=0
        self.ns_name = 'ns-%d' % index
        self.lns_name = 'lns-%d' % index
        self.ns_veth_name='vns-%d' % index
        self.lns_veth_name='vns-%d' % index

        ## OVS
        self.ovs_out_port = 1   ## Inbound flow to veth peer
        self.ovs_in_port = 2    ## Outbound flow - to eth2

        ## xl2tpd-related configuration
        self.xl2tpd_user = 'username'
        self.xl2tpd_password = 'password'
        self.xl2tpd_srv_ip='10.0.0.1'   ## Should be accepted from the DB
        self.xl2tpd_cln_ip='10.0.0.10'  ## Should be accepted from the
        self.xl2tpd_lac='172.31.230.2 - 172.31.230.254' ## Provider IP subnet
        self.lns_basedir='/etc/xl2tpd/' + self.lns_name
        self.f_xl2tpd_conf= self.lns_basedir + '/xl2tpd.conf'
        self.f_options_xl2tpd = self.lns_basedir + '/options.xl2tpd'
        self.f_chap_secret= self.lns_basedir + '/chap-secrets'
        self.f_xl2tpd_secret= self.lns_basedir + '/l2tp-secrets'
        self.f_xl2tpd_pid = self.lns_basedir + '/xl2tpd.pid'
        self.f_xl2tpd_ctrl = self.lns_basedir + '/xl2tpd-control'



        LOG.debug('L2TPTUN: init driver(%d): srv_ip = %s srv_port = %d',
            self.index, self.server_ip, self.server_port)



    def add(self, provider_ip, local_ip):
        if self.server_running:
            return False
        LOG.debug('L2TPTUN: add driver(%d) for despatching', self.index)
        self.server_running = 1
        return True


    def remove(self, provider_ip):
        if not self.server_running:
            return False
        LOG.debug('L2TPTUN: remove driver(%d) from dispatching', self.index)
        #D# import pdb; pdb.set_trace()
        ## Stop xl2tp/\s\+$d
        w = open(self.f_xl2tpd_pid, "r")
        pid = w.readline()
        w.close()
        hu.execute('kill', pid, run_as_root=True)

        ## Remove xl2tpd IS
        dir_delete(self.lns_basedir)

        ## Delete veth pairs
        veth_lns_peer="%s-01" % self.lns_name
        hu.delete_net_dev(veth_lns_peer)
        hu.delete_net_dev(self.veth2_lns_peer)

        ## Delete NetNS
        hu.netns_del(self.lns_name)
        self.server_running = 0

    def check_port_free(self, local_ip, port):
        return True

    ##
    # @brief All L2TP traffic to specified server
    #
    # @param parser
    #
    # @return
    def to_controller_match(self, parser):
        LOG.debug('L2TPTUN: for driver(%d): return initial match' , self.index)
        return parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_dst=self.server_ip,
                                udp_dst= self.server_port)

    def intercept_vpn_packets(self, parser, ofproto, provider_ip):
        LOG.debug('L2TPTUN: for driver(%d): return intercept data' , self.index)
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_dst=self.server_ip,
                                udp_dst= self.server_port),
                                [parser.OFPActionOutput(port=self.ovs_in_port)])

    def return_vpn_packets(self, parser, ofproto, provider_ip):
        LOG.debug('L2TPTUN: for driver(%d): return outbound data' , self.index)
        return (parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_src=self.server_ip,
                                udp_src= self.server_port),
                                [parser.OFPActionOutput(port=self.ovs_out_port)])

    def start_vpn(self, conn, br, vpn_nic_ip, br_nic):
        LOG.debug('L2TPTUN: for driver(%d): starting VPN callback' , self.index)

        ## Create Net NS for xl2tpd
        hu.netns_add(self.lns_name)

        ## Connect NetNS to BR-NIC by veth pair and
        ## configure l2tp server IP
        veth_lns_peer="%s-01" % self.lns_name
        veth_br_peer="%s-02" % self.lns_name
        hu.create_veth_pair(veth_lns_peer, veth_br_peer)
        hu.netns_move_to(self.lns_name, veth_lns_peer)
        hu.netns_exec(self.lns_name, 'ip', 'addr', 'add',
                        self.server_ip, 'dev', veth_lns_peer)
        hu.add_ovs_port(br_nic, veth_br_peer)

        ## Connect NetNS to linux bridge by veth pair
        self.veth2_lns_peer=conn.replace('tap', 'lns')
        veth2_qbr_peer= conn
        hu.create_veth_pair(self.veth2_lns_peer,veth2_qbr_peer)
        hu.netns_move_to(self.lns_name, self.veth2_lns_peer)
        hu.execute('brctl', 'addif', br, conn,
                   check_exit_code=False,
                   run_as_root=True)

        ## Ctrate IS for xl2tpd
        self.create_xl2tp_is(self.ns_name,
                            'my_host',
                            self.xl2tpd_cln_ip,
                            self.xl2tpd_srv_ip,
                            self.xl2tpd_lac)

        ## Start xl2tpd
        hu.netns_exec(self.lns_name,
                        '/usr/sbin/xl2tpd',
                        '-c', self.f_xl2tpd_conf,
                        '-p', self.f_xl2tpd_pid,
                        '-C', self.f_xl2tpd_ctrl)

        ## Configure routes
        ## TBD..

        return True

    def stop_vpn(self, tap):
        LOG.debug('L2TPTUN: for driver(%d): stopping VPN callback' , self.index)

    def create_xl2tp_is(self, ns_name, host_name, cln_peer_ip, srv_peer_ip, lac_range):

        hu.dir_create(self.lns_basedir)
        w = open(self.f_xl2tpd_conf, "w")
        w.write("\n".join(xl2tpd_conf) % (self.f_xl2tpd_secret,
                                            self.f_options_xl2tpd,
                                            host_name,
                                            cln_peer_ip,
                                            srv_peer_ip,
                                            lac_range))
        w.close()

        w = open(self.f_options_xl2tpd, "w")
        w.write("\n".join(options_l2tpd))
        w.close()


        w = open(self.f_chap_secret, "w")
        w.write(chap_secret % (self.xl2tpd_user, self.xl2tpd_password))
        w.close()

        w = open(self.f_xl2tpd_secret, "w")
        w.write(l2tp_secret % self.xl2tpd_password)
        w.close()

    def start_xl2tpd(self):
        pass
