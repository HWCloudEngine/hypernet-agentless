import socket

from oslo_config import cfg

from oslo_log import log as logging

import oslo_messaging

from hypernet_agentless import version
from hypernet_agentless._i18n import _
from hypernet_agentless.common import hs_constants


LOG = logging.getLogger(__name__)

# Default timeout for ovs-vsctl command
DEFAULT_OVS_VSCTL_TIMEOUT = 10

OPTS = [
    cfg.StrOpt('host', default=socket.gethostname(),
               sample_default='example.domain',
               help=_("Hostname to be used by the Hypernet server, agents and "
                      "services running on this machine. All the agents and "
                      "services running on this machine must use the same "
                      "host value.")),
    cfg.IntOpt('network_device_mtu',
               help=_('MTU setting for device. This option will be removed in '
                      'Newton. Please use the system-wide segment_mtu setting '
                      'which the agents will take into account when wiring '
                      'VIFs.')),
    cfg.StrOpt('rootwrap_config',
               default="/etc/hyperswitch/rootwrap.conf",
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
    cfg.IntOpt('ovs_vsctl_timeout',
               default=DEFAULT_OVS_VSCTL_TIMEOUT,
               help=_('Timeout in seconds for ovs-vsctl commands. '
                      'If the timeout expires, ovs commands will fail with '
                      'ALARMCLOCK error.')),
]
cfg.CONF.register_opts(OPTS)
OPTS_AGENT = [
    cfg.StrOpt('root_helper', default='sudo',
               help=_(
                   "Root helper application. Use "
                   "'sudo hyperswitch-rootwrap /etc/hyperswitch/rootwrap.conf'"
                   " to use the real root filter facility. Change to 'sudo' "
                   "to skip the filtering and just run the command directly."))
]
try:
    cfg.CONF.register_opts(OPTS_AGENT, 'AGENT')
except:
    pass


def init(args, **kwargs):
    product_name = "hyperswitch-agent"

    logging.register_options(cfg.CONF)
    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)
    oslo_messaging.set_transport_defaults(
        control_exchange=hs_constants.HYPERSWITCH)


    logging.setup(cfg.CONF, product_name)


def get_root_helper(conf):
    return conf.AGENT.root_helper
