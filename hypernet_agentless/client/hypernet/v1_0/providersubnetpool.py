
from hypernet_agentless._i18n import _
from hypernet_agentless.client.common import extension
from hypernet_agentless.client.hypernet.v1_0 import HypernetCommand


class Providersubnetpool(extension.HypernetClientExtension):
    resource = 'providersubnetpool'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class ProvidersubnetpoolCreate(
        extension.ClientExtensionCreate, Providersubnetpool):
    """Create an Providersubnetpool."""

    shell_command = 'providersubnetpool-create'

    def get_parser(self, prog_name):
        parser = HypernetCommand.get_parser(self, prog_name)
        self.add_known_arguments(parser)
        return parser

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--used-by', dest='used_by',
            help=_('tenant id using the provider subnet.'))
        parser.add_argument(
            'cidr', metavar='<CIDR>',
            help=_('provider subnet CIDR.'))

    def args2body(self, parsed_args):
        body = {'providersubnetpool':
            {
                'cidr': parsed_args.cidr,
            }
        }
        if parsed_args.used_by:
            body['providersubnetpool']['used_by'] = parsed_args.used_by
        return body


class ProvidersubnetpoolList(extension.ClientExtensionList,
                             Providersubnetpool):
    """List Providersubnetpool."""

    shell_command = 'providersubnetpool-list'
    list_columns = ['id', 'cidr', 'used_by', 'provider_subnet']
    pagination_support = True
    sorting_support = True


class ProvidersubnetpoolShow(extension.ClientExtensionShow,
                             Providersubnetpool):
    """Show information of a given Providersubnetpool."""

    shell_command = 'providersubnetpool-show'


class ProvidersubnetpoolDelete(extension.ClientExtensionDelete,
                               Providersubnetpool):
    """Delete a given Providersubnetpool."""

    shell_command = 'providersubnetpool-delete'


class ProvidersubnetpoolUpdate(
        extension.ClientExtensionUpdate, Providersubnetpool):
    """Update a given Providersubnetpool."""

    shell_command = 'providersubnetpool-update'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--used-by', dest='used_by',
            help=_('tenant id using the provider subnet.'))

    def args2body(self, parsed_args):
        body = {'providersubnetpool': {}}
        if parsed_args.used_by:
            body['providersubnetpool']['used_by'] = parsed_args.used_by
        return body


