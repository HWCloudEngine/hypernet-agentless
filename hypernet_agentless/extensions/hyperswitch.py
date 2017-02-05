import abc

from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron.api.v2 import resource_helper
from neutron.common import exceptions
from neutron.openstack.common import log as logging
from neutron.plugins.common import constants
from neutron.services import service_base

from hypernet_agentless import extensions as hypernet_agentless_extensions
from hypernet_agentless import hs_constants


extensions.append_api_extensions_path(hypernet_agentless_extensions.__path__)

constants.COMMON_PREFIXES[hs_constants.HYPERSWITCH] = '/'
constants.ALLOWED_SERVICES.append(hs_constants.HYPERSWITCH)


LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'agentlessports': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': False,
                 'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'required': True},
        'flavor': {'allow_post': True, 'allow_put': False,
                   'type:values': ['0G', '1G', '10G', None],
                   'is_visible': True, 'default': None},
        'device_id': {'allow_post': False, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'provider_ip': {'allow_post': True, 'allow_put': False,
                        'is_visible': True, 'default': None},
        'index': {'allow_post': True, 'allow_put': False,
                  'is_visible': True, 'convert_to': attributes.convert_to_int,
                  'type:values': [0, 1, 2, 3], 'default': 0,
                  'required': True},
        'user_data': {'allow_post': False, 'allow_put': False,
                      'is_visible': True},
        'provider': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
    },
    'hyperswitchs': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'required': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'is_visible': True},
        'device_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'flavor': {'allow_post': True, 'allow_put': False,
                   'is_visible': True, 'default': None},
        'instance_id': {'allow_post': True, 'allow_put': False,
                        'is_visible': True, 'default': None},
        'instance_type': {'allow_post': True, 'allow_put': False,
                          'is_visible': True, 'default': None},
        'mgnt_ip': {'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'default': None},
        'data_ip': {'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'default': None},
        'vms_ips': {'allow_post': True, 'allow_put': False,
                   'convert_to': attributes.convert_none_to_empty_list,
                   'default': None, 'is_visible': True},
        'provider': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
    },
}


class Hyperswitch(extensions.ExtensionDescriptor):

    """API extension for Hyperswitch."""

    @classmethod
    def get_name(cls):
        return 'Hyper Switch'

    @classmethod
    def get_alias(cls):
        return hs_constants.HYPERSWITCH

    @classmethod
    def get_description(cls):
        return "Hyper Switch Management."

    @classmethod
    def get_namespace(cls):
        return 'https://wiki.openstack.org'

    @classmethod
    def get_updated(cls):
        return '2016-12-01T00:00:00-00:00'

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        attributes.PLURALS.update(plural_mappings)
        resources = resource_helper.build_resource_info(
            plural_mappings,
            RESOURCE_ATTRIBUTE_MAP,
            hs_constants.HYPERSWITCH)
        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class HyperswitchPluginBase(service_base.ServicePluginBase):

    def get_plugin_type(self):
        """Get type of the plugin."""
        return hs_constants.HYPERSWITCH

    def get_plugin_name(self):
        """Get name of the plugin."""
        return hs_constants.HYPERSWITCH

    def get_plugin_description(self):
        """Get description of the plugin."""
        return "Hyperswitch Management Plugin"

    @abc.abstractmethod
    def create_agentlessport(self, context, agentlessport):
        pass

    @abc.abstractmethod
    def get_agentlessport(self, context, agentlessport_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_agentlessport(self, context, agentlessport_id):
        pass

    @abc.abstractmethod
    def get_agentlessports(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        pass

    @abc.abstractmethod
    def create_hyperswitch(self, context, hyperswitch):
        pass

    @abc.abstractmethod
    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        pass

    @abc.abstractmethod
    def update_hyperswitch(self,
                           context,
                           hyperswitch_id,
                           hyperswitch):
        pass

    @abc.abstractmethod
    def delete_hyperswitch(self, context, hyperswitch_id):
        pass

    @abc.abstractmethod
    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        pass


class HyperswitchNotFound(exceptions.NotFound):
    message = _('Hyperswitch %(hyperswitch_id)s could not be found.')


class HyperswitchProviderMultipleFound(exceptions.Conflict):
    message = _('Multiple hyper switches '
                '%(hyperswitch_id)s found in provider.')


class AgentlessPortNotFound(exceptions.NotFound):
    message = _('Agent less Port %(agentlessport_id)s could not be found.')


class AgentlessPortNeutronPortNotFound(exceptions.NotFound):
    message = _('Neutron port %(agentlessport_id)s found.')


class AgentlessPortNeutronPortMultipleFound(exceptions.Conflict):
    message = _('Multiple neutron ports for Agent less Port '
                '%(agentlessport_id)s found.')

class AgentlessPortProviderPortMultipleFound(exceptions.Conflict):
    message = _('Multiple provider ports for Agent less Port '
                '%(agentlessport_id)s found.')


class AgentlessPortBadDeviceId(exceptions.Conflict):
    message = _('Device id not match (received: %(device_id)s, '
                'neutron port: %(neutron_device_id)s).')