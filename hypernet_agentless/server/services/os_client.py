from keystoneauth1 import loading as ks_loading
from neutronclient.common import exceptions as neutron_client_exc
from neutronclient.v2_0 import client as clientv20
from novaclient import client as nova_client
from oslo_config import cfg

client_opts = [
    cfg.StrOpt('url',
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

CFG_INITED = set()
_ADMIN_AUTH = {}
_SESSION = {}


def _load_auth_plugin(conf, group):
    auth_plugin = ks_loading.load_auth_from_conf_options(conf, group)
    if auth_plugin:
        return auth_plugin

    err_msg = _('Unknown auth type: %s') % conf[group].auth_type
    raise neutron_client_exc.Unauthorized(message=err_msg)


def get_neutron_client(context=None, admin=False, group=NEUTRON_GROUP):
    if not group in CFG_INITED:
        CONF.register_opts(client_opts, group)
        _options = ks_loading.register_session_conf_options(CONF, group)
        ks_loading.register_auth_conf_options(CONF, group)
        CFG_INITED.add(group)

    auth_plugin = None

    if not group in _SESSION:
        _SESSION[group] = ks_loading.load_session_from_conf_options(
            CONF, group)

    if admin or (context.is_admin and not context.auth_token):
        if not group in _ADMIN_AUTH:
            _ADMIN_AUTH[group] = _load_auth_plugin(CONF, group)
        auth_plugin = _ADMIN_AUTH[group]

    elif context.auth_token:
        auth_plugin = context.get_auth_plugin()

    if not auth_plugin:
        # We did not get a user token and we should not be using
        # an admin token so log an error
        raise neutron_client_exc.Unauthorized()

    return clientv20.Client(session=_SESSION[group],
                            auth=auth_plugin,
                            endpoint_override=CONF[group].url,
                            region_name=CONF[group].region_name)

NOVA_CLIENTS = {}


def get_nova_client(conf_group):
    if conf_group in NOVA_CLIENTS:
        return NOVA_CLIENTS[conf_group]
    ks_loading.register_auth_conf_options(cfg.CONF, conf_group)
    ks_loading.register_session_conf_options(cfg.CONF, conf_group)
    auth_plugin = ks_loading.load_auth_from_conf_options(
        cfg.CONF, conf_group)
    auth_session = ks_loading.load_session_from_conf_options(
        cfg.CONF, conf_group)
    client = nova_client.Client('2.0',
        session=auth_session,
        auth=auth_plugin)
    NOVA_CLIENTS[conf_group] = client
    return client
