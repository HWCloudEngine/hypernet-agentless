import abc

from oslo_log import log as logging

from hypernet_agentless._i18n import _
from hypernet_agentless.common import hs_constants
from hypernet_agentless.common import exceptions
from hypernet_agentless.server.api import extensions
from hypernet_agentless.server.api.v1 import attributes
from hypernet_agentless.server.api.v1 import resource_helper
from hypernet_agentless.server.services import service_base


LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'providerports': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': False,
                 'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'is_visible': True, 'default': 'agentless'},
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
    'providersubnetpools': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': True,
                      'is_visible': True},
        'cidr': {'allow_post': True, 'allow_put': False,
                 'is_visible': True},
        'provider_subnet': {'allow_post': False, 'allow_put': False,
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
            RESOURCE_ATTRIBUTE_MAP)
        return resources

    def update_attributes_map(self, attributes):
        super(Hyperswitch, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        version_map = {'1.0': RESOURCE_ATTRIBUTE_MAP}
        return version_map.get(version, {})

    def get_plugin_interface(self):
        """Returns an abstract class which defines contract for the plugin.
        The abstract class should inherit from extesnions.PluginInterface,
        Methods in this abstract class  should be decorated as abstractmethod
        """
        return HyperswitchPluginBase


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
    def create_providerport(self, context, providerport):
        pass

    @abc.abstractmethod
    def get_providerport(self, context, providerport_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_providerport(self, context, providerport_id):
        pass

    @abc.abstractmethod
    def get_providerports(self, context, filters=None, fields=None,
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

    @abc.abstractmethod
    def create_providersubnetpool(self, context, providersubnetpool):
        pass

    @abc.abstractmethod
    def get_providersubnetpool(self,
                               context,
                               providersubnetpool_id,
                               fields=None):
        pass

    @abc.abstractmethod
    def update_providersubnetpool(self,
                                  context,
                                  providersubnetpool_id,
                                  providersubnetpool):
        pass

    @abc.abstractmethod
    def delete_providersubnetpool(self, context, providersubnetpool_id):
        pass

    @abc.abstractmethod
    def get_providersubnetpools(self, context, filters=None, fields=None,
                                sorts=None, limit=None, marker=None,
                                page_reverse=False):
        pass


class HyperswitchNotFound(exceptions.NotFound):
    message = _('Hyperswitch %(hyperswitch_id)s could not be found.')


class HyperswitchProviderMultipleFound(exceptions.Conflict):
    message = _('Multiple hyper switches '
                '%(hyperswitch_id)s found in provider.')


class HyperswitchVMCreationFailed(exceptions.Conflict):
    message = _('The Hyperswitch VM failed to be created %(hyperswitch_id),'
                '%(hyperswitch_status).')


class ProviderPortNotFound(exceptions.NotFound):
    message = _('Provider Port %(providerport_id)s could not be found.')


class ProviderPortNeutronPortNotFound(exceptions.NotFound):
    message = _('Neutron port not for Provider Port %(providerport_id)s.')


class ProviderPortNeutronPortMultipleFound(exceptions.Conflict):
    message = _('Multiple neutron ports found for Provider Port '
                '%(providerport_id)s.')


class ProviderPortProviderPortMultipleFound(exceptions.Conflict):
    message = _('Multiple provider ports for Provider Port '
                '%(providerport_id)s found.')


class ProviderPortBadDeviceId(exceptions.Conflict):
    message = _('Device id not match (received: %(device_id)s, '
                'neutron port: %(neutron_device_id)s).')