
import abc
import six

from hypernet_agentless.server.api import extensions


@six.add_metaclass(abc.ABCMeta)
class ServicePluginBase(extensions.PluginInterface):
    """Define base interface for any Advanced Service plugin."""
    supported_extension_aliases = []

    @abc.abstractmethod
    def get_plugin_type(self):
        """Return one of predefined service types.
        See hypernet/common/hs_constants.py
        """
        pass

    @abc.abstractmethod
    def get_plugin_name(self):
        """Return a symbolic name for the plugin.
        Each service plugin should have a symbolic name. This name
        will be used, for instance, by service definitions in service types
        """
        pass

    @abc.abstractmethod
    def get_plugin_description(self):
        """Return string description of the plugin."""
        pass