
from hypernet_agentless._i18n import _
from hypernet_agentless.client.common import exceptions
from hypernet_agentless.client.common import utils


API_NAME = 'hypernet'
API_VERSIONS = {
    '1.0': 'hypernet_agentless.client.v1_0.client.Client',
}


def make_client(instance):
    """Returns an hypernet client."""

    hypernet_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS,
    )
    instance.initialize()
    url = instance._url
    url = url.rstrip("/")
    if '1.0' == instance._api_version[API_NAME]:
        client = hypernet_client(username=instance._username,
                                 tenant_name=instance._tenant_name,
                                 password=instance._password,
                                 region_name=instance._region_name,
                                 auth_url=instance._auth_url,
                                 endpoint_url=url,
                                 endpoint_type=instance._endpoint_type,
                                 token=instance._token,
                                 auth_strategy=instance._auth_strategy,
                                 insecure=instance._insecure,
                                 ca_cert=instance._ca_cert,
                                 retries=instance._retries,
                                 raise_errors=instance._raise_errors,
                                 session=instance._session,
                                 auth=instance._auth)
        return client
    else:
        raise exceptions.UnsupportedVersion(_("API version %s is not "
                                              "supported") %
                                            instance._api_version[API_NAME])


def Client(api_version, *args, **kwargs):
    """Return an hypernet client.
    :param api_version: only 1.0 is supported now
    """
    hypernet_client = utils.get_client_class(
        API_NAME,
        api_version,
        API_VERSIONS,
    )
    return hypernet_client(*args, **kwargs)