
from neutronclient._i18n import _
from neutronclient.common import extension
from neutronclient.neutron.v2_0 import NeutronCommand


class Providerport(extension.NeutronClientExtension):
    resource = 'providerport'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class ProviderportCreate(extension.ClientExtensionCreate, Providerport):
    """Create an provider port information."""

    shell_command = 'providerport-create'

    def get_parser(self, prog_name):
        parser = NeutronCommand.get_parser(self, prog_name)
        self.add_known_arguments(parser)
        return parser

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', dest='name',
            help=_('Optional port name.'))
        parser.add_argument(
            '--flavor', dest='flavor',
            help=_('Network Flavor for the VM: 0G, 1G or 10G.'))
        parser.add_argument(
            '--device-id', dest='device_id',
            help=_('Optional Device ID of the port to create a '
                   'dedicated hyperswitch for this device.'))
        parser.add_argument(
            '--provider-ip', dest='provider_ip',
            help=_('Optional Provider IP for Null provider.'))
        parser.add_argument(
            'port_id', metavar='<NEUTRON_PORT_ID>',
            help=_('Neutron Port ID.'))
        parser.add_argument(
            'index', metavar='<INDEX>',
            help=_('Index of the port on the VM, begin from 0.'))

    def args2body(self, parsed_args):
        body = {'providerport':
            {
                'port_id': parsed_args.port_id,
                'index': parsed_args.index,
            }
        }
        if parsed_args.name:
            body['providerport']['name'] = parsed_args.name
        if parsed_args.flavor:
            body['providerport']['flavor'] = parsed_args.flavor
        if parsed_args.device_id:
            body['providerport']['device_id'] = parsed_args.device_id
        if parsed_args.provider_ip:
            body['providerport']['provider_ip'] = parsed_args.provider_ip
        return body


class ProviderportList(extension.ClientExtensionList, Providerport):
    """List provider ports that belongs to a given tenant."""

    shell_command = 'providerport-list'
    list_columns = ['id', 'port_id', 'device_id', 'tenant_id', 'index',
                    'user_data']
    pagination_support = True
    sorting_support = True


class ProviderportShow(extension.ClientExtensionShow, Providerport):
    """Show information of a given provider port."""

    shell_command = 'provider-show'


class ProviderportDelete(extension.ClientExtensionDelete, Providerport):
    """Delete a given provider port."""

    shell_command = 'provider-delete'
