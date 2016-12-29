import abc

from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron.api.v2 import resource_helper


RESOURCE_ATTRIBUTE_MAP = {
    'agentlessports': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'required': True},
        'flavor': {'allow_post': True, 'allow_put': False,
                   'type:values': ['0G', '1G', '10G', None],
                   'is_visible': True, 'default': None},
        'device_id': {'allow_post': False, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'index': {'allow_post': True, 'allow_put': False,
                  'is_visible': True, 'convert_to': attributes.convert_to_int,
                  'type:values': [0, 1, 2, 3],
                  'required': True},
        'user_data': {'allow_post': False, 'allow_put': False,
                      'is_visible': True},
    },
    'hyperswitchs': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'flavor': {'allow_post': True, 'allow_put': False,
                   'is_visible': True, 'required': True},
        'device_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'is_visible': True, 'required': True},
        'instance_id': {'allow_post': False, 'allow_put': False,
                        'is_visible': True},
        'instance_type': {'allow_post': False, 'allow_put': False,
                          'is_visible': True},
        'private_ip': {'allow_post': False, 'allow_put': False,
                       'is_visible': True},
        'mgnt_ip': {'allow_post': False, 'allow_put': False,
                    'is_visible': True},
        'data_ip': {'allow_post': False, 'allow_put': False,
                    'is_visible': True},
        'vms_ip_0': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
        'vms_ip_1': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
        'vms_ip_2': {'allow_post': False, 'allow_put': False,
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
        return 'hyperswitch'

    @classmethod
    def get_description(cls):
        return "Hyper Switch Management."

    @classmethod
    def get_updated(cls):
        return '2016-12-01T00:00:00-00:00'

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        resources = resource_helper.build_resource_info(plural_mappings,
                                                        RESOURCE_ATTRIBUTE_MAP,
                                                        'hyperswitch')

        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class HyperswitchPluginBase(object):

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
    def delete_hyperswitch(self, context, hyperswitch_id):
        pass

    @abc.abstractmethod
    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        pass
