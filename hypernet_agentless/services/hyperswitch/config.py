import socket

from hypernet_agentless import hs_constants
from hypernet_agentless._i18n import _

from oslo.config import cfg

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
    cfg.StrOpt('aws_access_key_id',
               help=_("AWS Access Key Id.")),
    cfg.StrOpt('aws_secret_access_key',
               help=_("AWS Secret Access Key.")),
    cfg.StrOpt('aws_region_name',
               help=_("AWS Region Name.")),
    cfg.StrOpt('aws_vpc',
               help=_("AWS VPC id.")),
    cfg.StrOpt('fs_username',
               help=_("The Openstack username.")),
    cfg.StrOpt('fs_password',
               help=_("The Openstack Password.")),
    cfg.StrOpt('fs_tenant_id',
               help=_("The Openstack Tenant Id.")),
    cfg.StrOpt('fs_auth_url',
               help=_("The Openstack Auth Url (keystone).")),
    cfg.StrOpt('fs_availability_zone',
               default='nova',
               help=_("The Openstack Availability zone.")),
    cfg.StrOpt('controller_ip',
               help=_("the controller ip.")),
    cfg.StrOpt('controller_name',
               help=_("a controller name.")),
    cfg.StrOpt('metadata_proxy_shared_secret',
               help=_("the metadata proxy share secret.")),
]


cfg.CONF.register_opts(OPTS_HYPERSWITCH, hs_constants.HYPERSWITCH)


def host():
    return cfg.CONF.host


def rabbit_hosts():
    rabbit_hosts = None
    for rabbit_host in cfg.CONF.rabbit_hosts:
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
    return cfg.CONF.rabbit_userid


def rabbit_password():
    return cfg.CONF.rabbit_password


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
    return cfg.CONF.hyperswitch.aws_access_key_id


def aws_secret_access_key():
    return cfg.CONF.hyperswitch.aws_secret_access_key


def aws_region_name():
    return cfg.CONF.hyperswitch.aws_region_name


def aws_vpc():
    return cfg.CONF.hyperswitch.aws_vpc


def fs_username():
    return cfg.CONF.hyperswitch.fs_username


def fs_password():
    return cfg.CONF.hyperswitch.fs_password


def fs_tenant_id():
    return cfg.CONF.hyperswitch.fs_tenant_id


def fs_auth_url():
    return cfg.CONF.hyperswitch.fs_auth_url


def fs_availability_zone():
    return cfg.CONF.hyperswitch.fs_availability_zone


def controller_ip():
    return cfg.CONF.hyperswitch.controller_ip


def controller_name():
    if cfg.CONF.hyperswitch.controller_name:
        return cfg.CONF.hyperswitch.controller_name
    return cfg.CONF.hyperswitch.controller_ip


def controller_host():
    if cfg.CONF.hyperswitch.controller_name:
        return '%s     %s' (
            cfg.CONF.hyperswitch.controller_ip,
            cfg.CONF.hyperswitch.controller_name
        )
    return ''


def metadata_proxy_shared_secret():
    return cfg.CONF.hyperswitch.metadata_proxy_shared_secret


def auth_uri():
    return cfg.CONF.keystone_authtoken.auth_uri


def auth_region():
    return cfg.CONF.keystone_authtoken.auth_region


def admin_tenant_name():
    return cfg.CONF.keystone_authtoken.admin_tenant_name


def admin_user():
    return cfg.CONF.keystone_authtoken.admin_user


def admin_password():
    return cfg.CONF.keystone_authtoken.admin_password
