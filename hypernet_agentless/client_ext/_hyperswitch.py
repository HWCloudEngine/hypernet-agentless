
from neutronclient._i18n import _
from neutronclient.common import extension
from neutronclient.common import utils

class HyperSwitch(extension.NeutronClientExtension):
    resource = 'hyperswitch'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class HyperSwitchCreate(extension.ClientExtensionCreate, HyperSwitch):
    """Create hyperswitch information."""

    shell_command = 'hyperswitch-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--device-id', dest='device_id',
            help=_('Device ID if created for one device.'))
        parser.add_argument(
            '--instance-id', dest='instance_id',
            help=_('Optional Instance ID (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            '--instance-type', dest='instance_type',
            help=_('Optional Instance Type (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            '--mgnt-ip', dest='mgnt_ip',
            help=_('Optional Management IP (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            '--data-ip', dest='data_ip',
            help=_('Optional Data IP (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            '--vms-ip', metavar='vms_ip=VMS_IP,index=INDEX',
            dest='vms_ips', action='append',
            type=utils.str2dict_type(required_keys=['vms_ip', 'index']),
            help=_('Optional VMs IP (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            'flavor', metavar='<FLAVOR>',
            help=_('VM network flavor: 0G, 1G or 10G.'))

    def args2body(self, parsed_args):
        body = {'hyperswitch': {'flavor': parsed_args.flavor}, }
        if parsed_args.tenant_id:
            body['hyperswitch']['tenant_id'] = parsed_args.tenant_id
        if parsed_args.device_id:
            body['hyperswitch']['device_id'] = parsed_args.device_id
        if parsed_args.instance_type:
            body['hyperswitch']['instance_type'] = parsed_args.instance_type
        if parsed_args.mgnt_ip:
            body['hyperswitch']['mgnt_ip'] = parsed_args.mgnt_ip
        if parsed_args.data_ip:
            body['hyperswitch']['data_ip'] = parsed_args.data_ip
        if parsed_args.vms_ips:
            body['hyperswitch']['vms_ips'] = parsed_args.vms_ips
        return body


class HyperSwitchList(extension.ClientExtensionList, HyperSwitch):
    """List hyperswitch that belongs to a given tenant."""

    shell_command = 'hyperswitch-list'
    list_columns = ['id', 'device_id', 'tenant_id', 'flavor']
    pagination_support = True
    sorting_support = True


class HyperSwitchShow(extension.ClientExtensionShow, HyperSwitch):
    """Show information of a given hyperswitch."""

    shell_command = 'hyperswitch-show'


class HyperSwitchDelete(extension.ClientExtensionDelete, HyperSwitch):
    """Delete a given hyperswitch."""

    shell_command = 'hyperswitch-delete'
