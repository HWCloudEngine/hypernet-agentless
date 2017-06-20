
from stevedore import extension

from hypernet_agentless.client.hypernet import v1_0 as hypernetV10


def _discover_via_entry_points():
    emgr = extension.ExtensionManager('hypernetclient.extension',
                                      invoke_on_load=False)
    return ((ext.name, ext.plugin) for ext in emgr)


class HypernetClientExtension(hypernetV10.HypernetCommand):
    pagination_support = False
    _formatters = {}
    sorting_support = False


class ClientExtensionShow(HypernetClientExtension, hypernetV10.ShowCommand):
    def get_data(self, parsed_args):
        # NOTE(mdietz): Calls 'execute' to provide a consistent pattern
        #               for any implementers adding extensions with
        #               regard to any other extension verb.
        return self.execute(parsed_args)

    def execute(self, parsed_args):
        return super(ClientExtensionShow, self).get_data(parsed_args)


class ClientExtensionList(HypernetClientExtension, hypernetV10.ListCommand):

    def get_data(self, parsed_args):
        # NOTE(mdietz): Calls 'execute' to provide a consistent pattern
        #               for any implementers adding extensions with
        #               regard to any other extension verb.
        return self.execute(parsed_args)

    def execute(self, parsed_args):
        return super(ClientExtensionList, self).get_data(parsed_args)


class ClientExtensionDelete(HypernetClientExtension,
                            hypernetV10.DeleteCommand):
    def run(self, parsed_args):
        # NOTE(mdietz): Calls 'execute' to provide a consistent pattern
        #               for any implementers adding extensions with
        #               regard to any other extension verb.
        return self.execute(parsed_args)

    def execute(self, parsed_args):
        return super(ClientExtensionDelete, self).run(parsed_args)


class ClientExtensionCreate(HypernetClientExtension,
                            hypernetV10.CreateCommand):
    def get_data(self, parsed_args):
        # NOTE(mdietz): Calls 'execute' to provide a consistent pattern
        #               for any implementers adding extensions with
        #               regard to any other extension verb.
        return self.execute(parsed_args)

    def execute(self, parsed_args):
        return super(ClientExtensionCreate, self).get_data(parsed_args)


class ClientExtensionUpdate(HypernetClientExtension,
                            hypernetV10.UpdateCommand):
    def run(self, parsed_args):
        # NOTE(mdietz): Calls 'execute' to provide a consistent pattern
        #               for any implementers adding extensions with
        #               regard to any other extension verb.
        return self.execute(parsed_args)

    def execute(self, parsed_args):
        return super(ClientExtensionUpdate, self).run(parsed_args)