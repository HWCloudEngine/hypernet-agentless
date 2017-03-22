
import logging
import requests
import time
import urlparse
import urllib

from hypernet_agentless._i18n import _
from hypernet_agentless.client import client
from hypernet_agentless.client.common import exceptions
from hypernet_agentless.client.common import serializer
from hypernet_agentless.client.common import utils


_logger = logging.getLogger(__name__)
DEFAULT_DESC_LENGTH = 25
DEFAULT_ERROR_REASON_LENGTH = 100


def exception_handler_v10(status_code, error_content):
    """Exception handler for API v1.0 client.
    This routine generates the appropriate Hypernet exception according to
    the contents of the response body.
    :param status_code: HTTP error status code
    :param error_content: deserialized body of error response
    """
    error_dict = None
    if isinstance(error_content, dict):
        error_dict = error_content.get('HypernetError')
    # Find real error type
    bad_hypernet_error_flag = False
    if error_dict:
        # If Tacker key is found, it will definitely contain
        # a 'message' and 'type' keys?
        try:
            error_type = error_dict['type']
            error_message = error_dict['message']
            if error_dict['detail']:
                error_message += "\n" + error_dict['detail']
        except Exception:
            bad_hypernet_error_flag = True
        if not bad_hypernet_error_flag:
            # If corresponding exception is defined, use it.
            client_exc = getattr(exceptions, '%sClient' % error_type, None)
            # Otherwise look up per status-code client exception
            if not client_exc:
                client_exc = exceptions.HTTP_EXCEPTION_MAP.get(status_code)
            if client_exc:
                raise client_exc(
                    message=error_message, status_code=status_code)
            else:
                raise exceptions.HypernetClientException(
                    status_code=status_code, message=error_message)
        else:
            raise exceptions.HypernetClientException(
                status_code=status_code, message=error_dict)
    else:
        message = None
        if isinstance(error_content, dict):
            message = error_content.get('message')
        if message:
            raise exceptions.HypernetClientException(
                status_code=status_code, message=message)

    # If we end up here the exception was not a tacker error
    msg = "%s-%s" % (status_code, error_content)
    raise exceptions.HypernetClientException(
        status_code=status_code, message=msg)


class APIParamsCall(object):
    """A Decorator to support formating and tenant overriding and filters."""

    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        def with_params(*args, **kwargs):
            _format = instance.format
            if 'format' in kwargs:
                instance.format = kwargs['format']
            ret = self.function(instance, *args, **kwargs)
            instance.format = _format
            return ret
        return with_params


class ClientBase(object):
    """Client for the OpenStack Tacker v1.0 API.
    :param string username: Username for authentication. (optional)
    :param string user_id: User ID for authentication. (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string tenant_name: Tenant name. (optional)
    :param string tenant_id: Tenant id. (optional)
    :param string auth_strategy: 'keystone' by default, 'noauth' for no
                                 authentication against keystone. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string service_type: Network service type to pull from the
                                keystone catalog (e.g. 'network') (optional)
    :param string endpoint_type: Network service endpoint type to pull from the
                                 keystone catalog (e.g. 'publicURL',
                                 'internalURL', or 'adminURL') (optional)
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint_url: A user-supplied endpoint URL for the tacker
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param bool insecure: SSL certificate validation. (optional)
    :param bool log_credentials: Allow for logging of passwords or not.
                                 Defaults to False. (optional)
    :param string ca_cert: SSL CA bundle file to use. (optional)
    :param integer retries: How many times idempotent (GET, PUT, DELETE)
                            requests to Tacker server should be retried if
                            they fail (default: 0).
    :param bool raise_errors: If True then exceptions caused by connection
                              failure are propagated to the caller.
                              (default: True)
    :param session: Keystone client auth session to use. (optional)
    :param auth: Keystone auth plugin to use. (optional)
    Example::
        from tackerclient.v1_0 import client
        tacker = client.Client(username=USER,
                                password=PASS,
                                tenant_name=TENANT_NAME,
                                auth_url=KEYSTONE_URL)
        nets = tacker.list_networks()
        ...
    """

    # API has no way to report plurals, so we have to hard code them
    # This variable should be overridden by a child class.
    EXTED_PLURALS = {}

    def __init__(self, **kwargs):
        """Initialize a new client for the Tacker v1.0 API."""
        super(ClientBase, self).__init__()
        self.retries = kwargs.pop('retries', 0)
        self.raise_errors = kwargs.pop('raise_errors', True)
        self.httpclient = client.construct_http_client(**kwargs)
        self.version = '1.0'
        self.format = 'json'
        self.action_prefix = "/v%s" % (self.version)
        self.retry_interval = 1

    def _handle_fault_response(self, status_code, response_body):
        # Create exception with HTTP status code and message
        _logger.debug("Error message: %s", response_body)
        # Add deserialized error message to exception arguments
        try:
            des_error_body = self.deserialize(response_body, status_code)
        except Exception:
            # If unable to deserialized body it is probably not a
            # Tacker error
            des_error_body = {'message': response_body}
        # Raise the appropriate exception
        exception_handler_v10(status_code, des_error_body)

    def do_request(self, method, action, body=None, headers=None, params=None):
        # Add format and tenant_id
        action += ".%s" % self.format
        action = self.action_prefix + action
        if type(params) is dict and params:
            params = utils.safe_encode_dict(params)
            action += '?' + urllib.urlencode(params, doseq=1)

        if body:
            body = self.serialize(body)

        resp, replybody = self.httpclient.do_request(
            action, method, body=body)

        status_code = resp.status_code
        if status_code in (requests.codes.ok,
                           requests.codes.created,
                           requests.codes.accepted,
                           requests.codes.no_content):
            return self.deserialize(replybody, status_code)
        else:
            if not replybody:
                replybody = resp.reason
            self._handle_fault_response(status_code, replybody)

    def get_auth_info(self):
        return self.httpclient.get_auth_info()

    def serialize(self, data):
        """Serializes a dictionary into either XML or JSON.
        A dictionary with a single key can be passed and it can contain any
        structure.
        """
        if data is None:
            return None
        elif type(data) is dict:
            return serializer.Serializer(
                self.get_attr_metadata()).serialize(data, self.content_type())
        else:
            raise Exception(_("Unable to serialize object of type = '%s'") %
                            type(data))

    def deserialize(self, data, status_code):
        """Deserializes an XML or JSON string into a dictionary."""
        if status_code == 204:
            return data
        return serializer.Serializer(self.get_attr_metadata()).deserialize(
            data, self.content_type())['body']

    def get_attr_metadata(self):
        if self.format == 'json':
            return {}

    def content_type(self, _format=None):
        """Returns the mime-type for either 'xml' or 'json'.
        Defaults to the currently set format.
        """
        _format = _format or self.format
        return "application/%s" % (_format)

    def retry_request(self, method, action, body=None,
                      headers=None, params=None):
        """Call do_request with the default retry configuration.
        Only idempotent requests should retry failed connection attempts.
        :raises: ConnectionFailed if the maximum # of retries is exceeded
        """
        max_attempts = self.retries + 1
        for i in range(max_attempts):
            try:
                return self.do_request(method, action, body=body,
                                       headers=headers, params=params)
            except exceptions.ConnectionFailed:
                # Exception has already been logged by do_request()
                if i < self.retries:
                    _logger.debug('Retrying connection to Tacker service')
                    time.sleep(self.retry_interval)
                elif self.raise_errors:
                    raise

        if self.retries:
            msg = (_("Failed to connect to Tacker server after %d attempts")
                   % max_attempts)
        else:
            msg = _("Failed to connect Tacker server")

        raise exceptions.ConnectionFailed(reason=msg)

    def delete(self, action, body=None, headers=None, params=None):
        return self.retry_request("DELETE", action, body=body,
                                  headers=headers, params=params)

    def get(self, action, body=None, headers=None, params=None):
        return self.retry_request("GET", action, body=body,
                                  headers=headers, params=params)

    def post(self, action, body=None, headers=None, params=None):
        # Do not retry POST requests to avoid the orphan objects problem.
        return self.do_request("POST", action, body=body,
                               headers=headers, params=params)

    def put(self, action, body=None, headers=None, params=None):
        return self.retry_request("PUT", action, body=body,
                                  headers=headers, params=params)

    def list(self, collection, path, retrieve_all=True, **params):
        if retrieve_all:
            res = []
            for r in self._pagination(collection, path, **params):
                res.extend(r[collection])
            return {collection: res}
        else:
            return self._pagination(collection, path, **params)

    def _pagination(self, collection, path, **params):
        if params.get('page_reverse', False):
            linkrel = 'previous'
        else:
            linkrel = 'next'
        next = True
        while next:
            res = self.get(path, params=params)
            yield res
            next = False
            try:
                for link in res['%s_links' % collection]:
                    if link['rel'] == linkrel:
                        query_str = urlparse.urlparse(link['href']).query
                        params = urlparse.parse_qs(query_str)
                        next = True
                        break
            except KeyError:
                break


class Client(ClientBase):

    hyperswitchs_path = '/hyperswitchs'
    hyperswitch_path = '/hyperswitchs/%s'

    providerports_path = '/providerports'
    providerport_path = '/providerports/%s'

    # API has no way to report plurals, so we have to hard code them
    # EXTED_PLURALS = {}

    @APIParamsCall
    def list_hyperswitchs(self, **_params):
        """Fetch a list of all hyperswitchs on server side."""
        return self.get(self.hyperswitchs_path, params=_params)

    @APIParamsCall
    def show_hyperswitch(self, hyperswitch, **_params):
        """Fetch a hyperswitch on server side."""
        return self.get(self.hyperswitch_path % hyperswitch, params=_params)

    @APIParamsCall
    def create_hyperswitch(self, body):
        return self.post(self.hyperswitchs_path, body)

    @APIParamsCall
    def delete_hyperswitch(self, hyperswitch):
        return self.delete(self.hyperswitch_path % hyperswitch)

    @APIParamsCall
    def list_providerports(self, **_params):
        """Fetch a list of all providerports on server side."""
        return self.get(self.providerports_path, params=_params)

    @APIParamsCall
    def show_providerport(self, providerport, **_params):
        """Fetch a providerport on server side."""
        return self.get(self.providerport_path % providerport, params=_params)

    @APIParamsCall
    def create_providerport(self, body):
        return self.post(self.providerports_path, body)

    @APIParamsCall
    def delete_providerport(self, providerport):
        return self.delete(self.providerport_path % providerport)

    @APIParamsCall
    def update_providerport(self, providerport, body):
        return self.put(self.providerport_path % providerport, body=body)
