from keystoneauth1 import loading as ks_loading
from neutronclient.common import exceptions as neutron_client_exc
from neutronclient.v2_0 import client as clientv20
from novaclient import client as nova_client
from oslo_config import cfg

neutron_opts = [
    cfg.StrOpt('url',
               default='http://127.0.0.1:9696',
               help='URL for connecting to neutron'),
    cfg.StrOpt('region_name',
               help='Region name for connecting to neutron in admin context'),
    cfg.StrOpt('ovs_bridge',
               default='br-int',
               help='Default OVS bridge name to use if not specified '
                    'by Neutron'),
    cfg.IntOpt('extension_sync_interval',
                default=600,
                help='Number of seconds before querying neutron for'
                     ' extensions'),
   ]

_SESSION = None
_ADMIN_AUTH = None

NEUTRON_GROUP = 'neutron'

CONF = cfg.CONF
CONF.register_opts(neutron_opts, NEUTRON_GROUP)

deprecations = {'cafile': [cfg.DeprecatedOpt('ca_certificates_file',
                                             group=NEUTRON_GROUP)],
                'insecure': [cfg.DeprecatedOpt('api_insecure',
                                               group=NEUTRON_GROUP)],
                'timeout': [cfg.DeprecatedOpt('url_timeout',
                                              group=NEUTRON_GROUP)]}

_neutron_options = ks_loading.register_session_conf_options(
    CONF, NEUTRON_GROUP, deprecated_opts=deprecations)
ks_loading.register_auth_conf_options(CONF, NEUTRON_GROUP)

def _load_auth_plugin(conf):
    auth_plugin = ks_loading.load_auth_from_conf_options(conf, NEUTRON_GROUP)

    if auth_plugin:
        return auth_plugin

    err_msg = _('Unknown auth type: %s') % conf.neutron.auth_type
    raise neutron_client_exc.Unauthorized(message=err_msg)

def get_neutron_client(context, admin=False):
    global _ADMIN_AUTH
    global _SESSION

    auth_plugin = None

    if not _SESSION:
        _SESSION = ks_loading.load_session_from_conf_options(
            CONF, NEUTRON_GROUP)

    if admin or (context.is_admin and not context.auth_token):
        if not _ADMIN_AUTH:
            _ADMIN_AUTH = _load_auth_plugin(CONF)
        auth_plugin = _ADMIN_AUTH

    elif context.auth_token:
        auth_plugin = context.get_auth_plugin()

    if not auth_plugin:
        # We did not get a user token and we should not be using
        # an admin token so log an error
        raise neutron_client_exc.Unauthorized()

    return clientv20.Client(session=_SESSION,
                            auth=auth_plugin,
                            endpoint_override=CONF.neutron.url,
                            region_name=CONF.neutron.region_name)

NOVA_CLIENTS = {}


def get_nova_client(conf_group):
    if conf_group in NOVA_CLIENTS:
        return NOVA_CLIENTS[conf_group]
    loading.register_auth_conf_options(cfg.CONF, conf_group)
    loading.register_session_conf_options(cfg.CONF, conf_group)
    auth_plugin = loading.load_auth_from_conf_options(
        cfg.CONF, conf_group)
    auth_session = loading.load_session_from_conf_options(
        cfg.CONF, conf_group)
    client = nova_client.Client('2.0',
        session=auth_session,
        auth=auth_plugin)
    NOVA_CLIENTS[conf_group] = client
    return client
