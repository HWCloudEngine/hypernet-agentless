
from neutronclient._i18n import _
from neutronclient.common import extension

from hypernet_agentless import hs_constants


class HyperSwitch(extension.NeutronClientExtension):
    resource = hs_constants.HYPERSWITCH
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
            '--vms_ip', dest='vms_ips', action='append',
            help=_('Optional VMs IP (when not managed by '
                   'the provider driver).'))
        parser.add_argument(
            'flavor', metavar='<FLAVOR>',
            help=_('VM network flavor: 0G, 1G or 10G.'))

    def args2body(self, parsed_args):
        body = {hs_constants.HYPERSWITCH: {'flavor': parsed_args.flavor}, }
        if parsed_args.tenant_id:
            body[hs_constants.HYPERSWITCH]['tenant_id'] = parsed_args.tenant_id
        if parsed_args.device_id:
            body[hs_constants.HYPERSWITCH]['device_id'] = parsed_args.device_id
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
