import socket

from hypernet_agentless.common import hs_constants
from hypernet_agentless import version
from hypernet_agentless._i18n import _

from hypernet_agentless.server import rpc

from oslo_config import cfg

from oslo_log import log as logging

from oslo_service import service
from oslo_service import sslutils
from oslo_service import wsgi


OPTS = [
    cfg.StrOpt('host', default=socket.gethostname(),
               help=_("The hostname hypernet is running on")),
    cfg.IPOpt('bind_host', default='0.0.0.0',
              help=_("The host IP to bind to")),
    cfg.PortOpt('bind_port', default=8333,
                help=_("The port to bind to")),
    cfg.StrOpt('auth_strategy', default='keystone',
               help=_("The type of authentication to use")),
    cfg.IntOpt('api_workers',
               help=_('Number of separate API worker processes for service. '
                      'If not specified, the default is equal to the number '
                      'of CPUs available for best performance.')),
    cfg.IntOpt('rpc_workers',
               default=1,
               help=_('Number of RPC worker processes for service.')),
    cfg.BoolOpt('allow_bulk', default=True,
                help=_("Allow the usage of the bulk API")),
    cfg.BoolOpt('allow_pagination', default=False,
                help=_("Allow the usage of the pagination")),
    cfg.BoolOpt('allow_sorting', default=False,
                help=_("Allow the usage of the sorting")),
    cfg.StrOpt('pagination_max_limit', default="-1",
               help=_("The maximum number of items returned in a single "
                      "response, value was 'infinite' or negative integer "
                      "means no limit")),
    cfg.ListOpt('service_plugins', default=['hyperswitch'],
            help=_("The service plugins Tacker will use")),
    cfg.StrOpt('api_extensions_path', default="",
               help=_("The path for API extensions")),
]


OPTS_HYPERSWITCH = [
    cfg.StrOpt('provider', default='null',
               help=_("Provider: aws|openstack|null.")),
    cfg.StrOpt('level', default='tenant',
               help=_("Level: tenant|vm.")),
    cfg.StrOpt('fip_network',
               help=_("FIP network id or name.")),
    cfg.StrOpt('fip_security_group',
               help=_("FIP network security group id or name.")),
    cfg.StrOpt('mgnt_network',
               help=_("Management network id or name.")),
    cfg.StrOpt('mgnt_security_group',
               help=_("Management network security group id or name.")),
    cfg.StrOpt('data_network',
               help=_("Data network id or name.")),
    cfg.StrOpt('data_security_group',
               help=_("Data network security group id or name.")),
    cfg.StrOpt('hs_default_flavor',
               default='high',
               help=_("Default flavor for hyperswitch creation.")),
    cfg.StrOpt('tenant_subnet_pool_first_cidr',
               help='The first provider cidr to create in'
                    ' the provider subnet pool.'),
    cfg.IntOpt('tenant_subnet_pool_nb',
               help='The number of provider subnet to create in the pool.'),
    cfg.DictOpt('hs_flavor_map',
# AWS default
               default={'low': 't2.micro', 'moderate': 'c3.large',
                        'high': 'm3.xlarge', '10G': 'c3.8xlarge',
                        '20G': 'r4.16xlarge'},
                help=_("HyperSwitch flavor Map")),
    cfg.StrOpt('controller_ip',
               help=_("the controller ip.")),
    cfg.StrOpt('controller_name',
               help=_("a controller name.")),
    cfg.StrOpt('meta_auth_region',
               help=_("The auth Region for metadata agent.")),
    cfg.StrOpt('meta_metadata_proxy_shared_secret',
               help=_("the metadata proxy share secret.")),
    cfg.StrOpt('meta_auth_uri',
               help=_("the metadata auth_uri.")),
    cfg.StrOpt('meta_admin_tenant_name',
               help=_("the metadata admin_tenant_name.")),
    cfg.StrOpt('meta_admin_user',
               help=_("the metadata admin_user.")),
    cfg.StrOpt('meta_admin_password',
               help=_("the metadata admin_password.")),
    cfg.IntOpt('first_openvpn_port',
               default=1194,
               help='The first port for OpenVPN connection'),
    cfg.IntOpt('max_win_nics',
               default=20,
               help='The max number of supported NICs in windows.'),
    cfg.StrOpt('hyperswitch_img_tag_value',
               default='hyperswitch',
               help='The tag value of the image of the hyperswitch.'),
    cfg.StrOpt('hyperswitch_prefix',
               default='hyperswitch',
               help='The value of the hyperswitch name, i.e. prefix@id.'),
]

OPTS_HYPERSWITCH_AWS = [
    cfg.StrOpt('access_key_id',
               help=_("AWS Access Key Id.")),
    cfg.StrOpt('secret_access_key',
               help=_("AWS Secret Access Key.")),
    cfg.StrOpt('region_name',
               help=_("AWS Region Name.")),
    cfg.StrOpt('vpc',
               help=_("AWS VPC id.")),
]

OPTS_HYPERSWITCH_FS = [
    cfg.StrOpt('availability_zone',
               default='nova',
               help=_("The Openstack Availability zone.")),
]

OPTS_DATABASE = [
    cfg.StrOpt('engine',
               default='',
               help=_('Database engine')),
]

cfg.CONF.register_opts(OPTS)
cfg.CONF.register_opts(OPTS_HYPERSWITCH, hs_constants.HYPERSWITCH)
cfg.CONF.register_opts(OPTS_HYPERSWITCH_AWS, hs_constants.HYPERSWITCH + '_aws')
cfg.CONF.register_opts(OPTS_HYPERSWITCH_FS, hs_constants.HYPERSWITCH + '_fs')
cfg.CONF.register_cli_opts(OPTS_DATABASE, 'database')


def init(args, **kwargs):
    product_name = 'hypernet_agentless'

    logging.register_options(cfg.CONF)

    wsgi.register_opts(cfg.CONF)
    cfg.CONF.register_opts(service.list_opts()[0][1])
    sslutils.register_opts(cfg.CONF)

    cfg.CONF(args=args, project=product_name,
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)

    logging.setup(cfg.CONF, product_name)
    rpc.init(cfg.CONF)


def load_paste_app(app_name):
    """Builds and returns a WSGI app from a paste config file.

    :param app_name: Name of the application to load
    """
    loader = wsgi.Loader(cfg.CONF)
    app = loader.load_app(app_name)
    return app


def host():
    return cfg.CONF.host


def rabbit_hosts():
    rabbit_hosts = None
    for rabbit_host in cfg.CONF.oslo_messaging_rabbit.rabbit_hosts:
        # translate to ip
        if ':' in rabbit_host:
            a = rabbit_host.split(':')
            h = a[0]
            p = a[1]
        else:
            h = rabbit_host
            p = 5672
        h = socket.getaddrinfo(h, p)[2][4][0]
        rabbit_host = '%s:%s' % (h, p)
        if rabbit_hosts:
            rabbit_hosts = '%s, %s' % (rabbit_hosts, rabbit_host)
        else:
            rabbit_hosts = rabbit_host
    return rabbit_hosts


def rabbit_userid():
    return cfg.CONF.oslo_messaging_rabbit.rabbit_userid


def rabbit_password():
    return cfg.CONF.oslo_messaging_rabbit.rabbit_password


def provider():
    return cfg.CONF.hyperswitch.provider


def level():
    return cfg.CONF.hyperswitch.level

def fip_network():
    return cfg.CONF.hyperswitch.fip_network


def fip_security_group():
    return cfg.CONF.hyperswitch.mgnt_security_group

def mgnt_network():
    return cfg.CONF.hyperswitch.mgnt_network


def mgnt_security_group():
    return cfg.CONF.hyperswitch.mgnt_security_group


def data_network():
    return cfg.CONF.hyperswitch.data_network


def data_security_group():
    return cfg.CONF.hyperswitch.data_security_group


def hs_default_flavor():
    return cfg.CONF.hyperswitch.hs_default_flavor


def tenant_subnet_pool_first_cidr():
    return cfg.CONF.hyperswitch.tenant_subnet_pool_first_cidr


def tenant_subnet_pool_nb():
    return cfg.CONF.hyperswitch.tenant_subnet_pool_nb


def hs_flavor_map():
    return cfg.CONF.hyperswitch.hs_flavor_map


def aws_access_key_id():
    return cfg.CONF.hyperswitch_aws.access_key_id


def aws_secret_access_key():
    return cfg.CONF.hyperswitch_aws.secret_access_key


def aws_region_name():
    return cfg.CONF.hyperswitch_aws.region_name


def aws_vpc():
    return cfg.CONF.hyperswitch_aws.vpc


def fs_tenant_id():
    return cfg.CONF.hyperswitch_fs.tenant_id


def fs_availability_zone():
    return cfg.CONF.hyperswitch_fs.availability_zone


def controller_ip():
    return cfg.CONF.hyperswitch.controller_ip


def controller_name():
    if cfg.CONF.hyperswitch.controller_name:
        return cfg.CONF.hyperswitch.controller_name
    return cfg.CONF.hyperswitch.controller_ip


def controller_host():
    if cfg.CONF.hyperswitch.controller_name:
        return '%s     %s' % (
            cfg.CONF.hyperswitch.controller_ip,
            cfg.CONF.hyperswitch.controller_name
        )
    return ''


def meta_auth_region():
    if cfg.CONF.hyperswitch.meta_auth_region:
        return cfg.CONF.hyperswitch.meta_auth_region
    return cfg.CONF.nova_region_name


def meta_metadata_proxy_shared_secret():
    return cfg.CONF.hyperswitch.meta_metadata_proxy_shared_secret


def meta_auth_uri():
    if cfg.CONF.hyperswitch.meta_auth_uri:
        return cfg.CONF.hyperswitch.meta_auth_uri
    return cfg.CONF.keystone_authtoken.auth_uri


def meta_admin_tenant_name():
    if cfg.CONF.hyperswitch.meta_admin_tenant_name:
        return cfg.CONF.hyperswitch.meta_admin_tenant_name
    return cfg.CONF.keystone_authtoken.admin_tenant_name


def meta_admin_user():
    if cfg.CONF.hyperswitch.meta_admin_user:
        return cfg.CONF.hyperswitch.meta_admin_user
    return cfg.CONF.keystone_authtoken.admin_user


def meta_admin_password():
    if cfg.CONF.hyperswitch.meta_admin_password:
        return cfg.CONF.hyperswitch.meta_admin_password
    return cfg.CONF.keystone_authtoken.admin_password


def first_openvpn_port():
    return cfg.CONF.hyperswitch.first_openvpn_port


def max_win_nics():
    return cfg.CONF.hyperswitch.max_win_nics


def hyperswitch_img_tag_value():
    return cfg.CONF.hyperswitch.hyperswitch_img_tag_value


def hyperswitch_prefix():
    return cfg.CONF.hyperswitch.hyperswitch_prefix
