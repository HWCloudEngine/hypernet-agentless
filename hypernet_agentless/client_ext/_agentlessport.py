from neutronclient.common import extension
from neutronclient.neutron.v2_0 import NeutronCommand
from hypernet_agentless._i18n import _


class Agentlessport(extension.NeutronClientExtension):
    resource = 'agentlessport'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class AgentlessportCreate(extension.ClientExtensionCreate, Agentlessport):
    """Create an agentless port information."""

    shell_command = 'agentlessport-create'

    def get_parser(self, prog_name):
        parser = NeutronCommand.get_parser(self, prog_name)
        self.add_known_arguments(parser)
        return parser

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', dest='name',
            help=_('OPtional port name.'))
        parser.add_argument(
            '--flavor', dest='flavor',
            help=_('Network Flavor for the VM: 0G, 1G or 10G.'))
        parser.add_argument(
            '--device-id', dest='device_id',
            help=_('Optional Device ID of the port to create a '
                   'dedicated hyperswitch for this device.'))
        parser.add_argument(
            'port_id', metavar='<NEUTRON_PORT_ID>',
            help=_('Neutron Port ID.'))
        parser.add_argument(
            'index', metavar='<INDEX>',
            help=_('Index of the port on the VM, begin from 0.'))

    def args2body(self, parsed_args):
        body = {'agentlessport':
            {
                'port_id': parsed_args.port_id,
                'index': parsed_args.index,
            }
        }
        if parsed_args.flavor:
            body['agentlessport']['flavor'] = parsed_args.flavor
        if parsed_args.device_id:
            body['agentlessport']['device_id'] = parsed_args.device_id
        return body


class AgentlessportList(extension.ClientExtensionList, Agentlessport):
    """List agentless ports that belongs to a given tenant."""

    shell_command = 'agentlessport-list'
    list_columns = ['id', 'port_id', 'device_id', 'tenant_id', 'index',
                    'user_data']
    pagination_support = True
    sorting_support = True


class AgentlessportShow(extension.ClientExtensionShow, Agentlessport):
    """Show information of a given agentless port."""

    shell_command = 'agentlessport-show'


class AgentlessportDelete(extension.ClientExtensionDelete, Agentlessport):
    """Delete a given agentless port."""

    shell_command = 'agentlessport-delete'
