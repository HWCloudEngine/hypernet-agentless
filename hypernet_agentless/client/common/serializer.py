
import json
import logging
import six

from hypernet_agentless._i18n import _
from hypernet_agentless.client.common import exceptions
from hypernet_agentless.client.common import utils


LOG = logging.getLogger(__name__)


class ActionDispatcher(object):
    """Maps method name to local methods through action name."""

    def dispatch(self, *args, **kwargs):
        """Find and call local method."""
        action = kwargs.pop('action', 'default')
        action_method = getattr(self, str(action), self.default)
        return action_method(*args, **kwargs)

    def default(self, data):
        raise NotImplementedError()


class DictSerializer(ActionDispatcher):
    """Default request body serialization."""

    def serialize(self, data, action='default'):
        return self.dispatch(data, action=action)

    def default(self, data):
        return ""


class JSONDictSerializer(DictSerializer):
    """Default JSON request body serialization."""

    def default(self, data):
        def sanitizer(obj):
            return six.text_type(obj)
        return json.dumps(data, default=sanitizer)


class TextDeserializer(ActionDispatcher):
    """Default request body deserialization."""

    def deserialize(self, datastring, action='default'):
        return self.dispatch(datastring, action=action)

    def default(self, datastring):
        return {}


class JSONDeserializer(TextDeserializer):

    def _from_json(self, datastring):
        try:
            return json.loads(utils.safe_decode(
                datastring), encoding='utf-8')
        except ValueError:
            msg = _("Cannot understand JSON")
            raise exceptions.MalformedResponseBody(reason=msg)

    def default(self, datastring):
        return {'body': self._from_json(datastring)}


# NOTE(maru): this class is duplicated from tacker.wsgi
class Serializer(object):
    """Serializes and deserializes dictionaries to certain MIME types."""

    def __init__(self, metadata=None, default_xmlns=None):
        """Create a serializer based on the given WSGI environment.
        'metadata' is an optional dict mapping MIME types to information
        needed to serialize a dictionary to that type.
        """
        self.metadata = metadata or {}
        self.default_xmlns = default_xmlns

    def _get_serialize_handler(self, content_type):
        handlers = {
            'application/json': JSONDictSerializer(),
        }

        try:
            return handlers[content_type]
        except Exception:
            raise exceptions.InvalidContentType(content_type=content_type)

    def serialize(self, data, content_type):
        """Serialize a dictionary into the specified content type."""
        return self._get_serialize_handler(content_type).serialize(data)

    def deserialize(self, datastring, content_type):
        """Deserialize a string to a dictionary.
        The string must be in the format of a supported MIME type.
        """
        return self.get_deserialize_handler(content_type).deserialize(
            datastring)

    def get_deserialize_handler(self, content_type):
        handlers = {
            'application/json': JSONDeserializer(),
        }

        try:
            return handlers[content_type]
        except Exception:
            raise exceptions.InvalidContentType(content_type=content_type)