
from oslo_config import cfg

from hypernet_agentless.common import hs_constants
from hypernet_agentless.server import manager
from hypernet_agentless.server.api import extensions
from hypernet_agentless.server.api.v1 import base


def build_plural_mappings(special_mappings, resource_map):
    """Create plural to singular mapping for all resources.
    Allows for special mappings to be provided, like policies -> policy.
    Otherwise, will strip off the last character for normal mappings, like
    routers -> router.
    """
    plural_mappings = {}
    for plural in resource_map:
        singular = special_mappings.get(plural, plural[:-1])
        plural_mappings[plural] = singular
    return plural_mappings


def build_resource_info(plural_mappings,
                        resource_map,
                        which_service=hs_constants.HYPERSWITCH,
                        action_map=None,
                        translate_name=False, allow_bulk=False):
    """Build resources for advanced services.
    Takes the resource information, and singular/plural mappings, and creates
    API resource objects for advanced services extensions. Will optionally
    translate underscores to dashes in resource names, register the resource,
    and accept action information for resources.
    :param plural_mappings: mappings between singular and plural forms
    :param resource_map: attribute map for the WSGI resources to create
    :param which_service: The name of the service for which the WSGI resources
                          are being created. This name will be used to pass
                          the appropriate plugin to the WSGI resource.
                          It can be set to None or "CORE"to create WSGI
                          resources for the core plugin
    :param action_map: custom resource actions
    :param translate_name: replaces underscores with dashes
    :param allow_bulk: True if bulk create are allowed
    """
    resources = []
    action_map = action_map or {}
    plugin = manager.HypernetManager.get_service_plugins()[which_service]
    for collection_name in resource_map:
        resource_name = plural_mappings[collection_name]
        params = resource_map.get(collection_name, {})
        if translate_name:
            collection_name = collection_name.replace('_', '-')
        member_actions = action_map.get(resource_name, {})
        controller = base.create_resource(
            collection_name, resource_name, plugin, params,
            member_actions=member_actions,
            allow_bulk=allow_bulk,
            allow_pagination=cfg.CONF.allow_pagination,
            allow_sorting=cfg.CONF.allow_sorting)
        resource = extensions.ResourceExtension(
            collection_name,
            controller,
            path_prefix=hs_constants.COMMON_PREFIXES[which_service],
            member_actions=member_actions,
            attr_map=params)
        resources.append(resource)
    return resources
