from keystoneauth1 import loading

from neutronclient.v2_0 import client as neutron_client

from novaclient import client as nova_client

from oslo_config import cfg


NEUTRON_CLIENTS = {}


def get_neutron_client(conf_group):
    if conf_group in NEUTRON_CLIENTS:
        return NEUTRON_CLIENTS[conf_group]
    loading.register_auth_conf_options(cfg.CONF, conf_group)
    loading.register_session_conf_options(cfg.CONF, conf_group)
    auth_plugin = loading.load_auth_from_conf_options(
        cfg.CONF, conf_group)
    auth_session = loading.load_session_from_conf_options(
        cfg.CONF, conf_group)
    client = neutron_client.Client(
        session=auth_session,
        auth=auth_plugin)
    NEUTRON_CLIENTS[conf_group] = client
    return client


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
