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
    cfg.StrOpt('mgnt_network',
               help=_("Management network id or name.")),
    cfg.StrOpt('mgnt_security_group',
               help=_("Management network security group id or name.")),
    cfg.StrOpt('data_network',
               help=_("Data network id or name.")),
    cfg.StrOpt('data_security_group',
               help=_("Data network security group id or name.")),
    cfg.ListOpt('vms_networks',
               help=_("VMs networks id or name list "
                      " for not automatic creation.")),
    cfg.ListOpt('vms_cidr', default=['172.31.192.0/20',
                                     '172.31.208.0/20',
                                     '172.31.224.0/20'],
               help=_("Data network security group id or name.")),
    cfg.StrOpt('hs_sg_name',
               default='hs_sg_vms_123456',
               help=_("Hyper Switch Security Group Name for VPN Server NICS.")),
    cfg.StrOpt('vm_sg_name',
               default='vm_sg_vms_123456',
               help=_("Provider Security Group Name for agent less NICs.")),
    cfg.StrOpt('hs_default_flavor', default='1G',
               help=_("Default flavor for hyperswitch creation.")),
    cfg.DictOpt('hs_flavor_map',
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
    product_name = 'hypernet'
    
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
        h = socket.gethostbyname_ex(h)[2][0]
        if ':' in rabbit_host:
            rabbit_host = '%s:%s' % (h, p)
        else:
            rabbit_host = h
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


def mgnt_network():
    return cfg.CONF.hyperswitch.mgnt_network


def mgnt_security_group():
    return cfg.CONF.hyperswitch.mgnt_security_group


def data_network():
    return cfg.CONF.hyperswitch.data_network


def data_security_group():
    return cfg.CONF.hyperswitch.data_security_group


def vms_networks():
    return cfg.CONF.hyperswitch.vms_networks


def vms_cidr():
    return cfg.CONF.hyperswitch.vms_cidr


def hs_sg_name():
    return cfg.CONF.hyperswitch.hs_sg_name


def vm_sg_name():
    return cfg.CONF.hyperswitch.vm_sg_name


def hs_default_flavor():
    return cfg.CONF.hyperswitch.hs_default_flavor


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
