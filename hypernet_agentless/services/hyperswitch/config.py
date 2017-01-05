
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
    cfg.StrOpt('default_flavor', default='1G',
               help=_("Default flavor for hyperswitch creation.")),
    cfg.StrOpt('aws_access_key_id',
               help=_("AWS Access Key Id.")),
    cfg.StrOpt('aws_secret_access_key',
               help=_("AWS Secret Access Key.")),
    cfg.StrOpt('aws_region_name',
               help=_("AWS Region Name.")),
    cfg.DictOpt('aws_hs_flavor_map',
                default={'0G': 't2.micro',
                         '1G': 'c4.large',
                         '10G': 'c4.xlarge'},
                help=_("AWS HyperSwitch flavor Map")),
    cfg.StrOpt('aws_vpc',
               help=_("AWS VPC id.")),
]


cfg.CONF.register_opts(OPTS_HYPERSWITCH, 'hyperswitch')


def get_host():
    return cfg.CONF.host


def get_rabbit_hosts():
    return cfg.CONF.oslo_messaging_rabbit.rabbit_hosts


def get_rabbit_userid():
    return cfg.CONF.oslo_messaging_rabbit.rabbit_userid


def get_rabbit_password():
    return cfg.CONF.oslo_messaging_rabbit.rabbit_password


def get_provider():
    return cfg.CONF.hyperswitch.provider


def get_level():
    return cfg.CONF.hyperswitch.level


def get_mgnt_network():
    return cfg.CONF.hyperswitch.mgnt_network


def get_mgnt_security_group():
    return cfg.CONF.hyperswitch.mgnt_security_group


def get_data_network():
    return cfg.CONF.hyperswitch.data_network


def get_data_security_group():
    return cfg.CONF.hyperswitch.data_security_group


def get_vms_networks():
    return cfg.CONF.hyperswitch.vms_networks


def get_vms_cidr():
    return cfg.CONF.hyperswitch.vms_cidr


def get_hs_sg_name():
    return cfg.CONF.hyperswitch.hs_sg_name


def get_vm_sg_name():
    return cfg.CONF.hyperswitch.vm_sg_name


def get_default_flavor():
    return cfg.CONF.hyperswitch.default_flavor


def get_aws_access_key_id():
    return cfg.CONF.hyperswitch.aws_access_key_id


def get_aws_secret_access_key():
    return cfg.CONF.hyperswitch.aws_secret_access_key


def get_aws_region_name():
    return cfg.CONF.hyperswitch.aws_region_name


def get_aws_hs_flavor_map():
    return cfg.CONF.hyperswitch.aws_hs_flavor_map


def get_aws_vpc():
    return cfg.CONF.hyperswitch.aws_vpc
