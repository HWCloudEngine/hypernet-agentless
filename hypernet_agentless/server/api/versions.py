import os
import webob.dec

from hypernet_agentless.server.api import wsgi


class Versions(object):

    @classmethod
    def factory(cls, global_config, **local_config):
        return cls()

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        """Respond to a request for all Hypernet API versions."""
        version_objs = [
            {
                "id": "v1.0",
                "status": "CURRENT",
            },
        ]

        if req.path != '/':
            return webob.exc.HTTPNotFound(
                explanation='Unknown API version specified')

        builder = get_view_builder(req)
        versions = [builder.build(version) for version in version_objs]
        response = dict(versions=versions)
        metadata = {
            "application/xml": {
                "attributes": {
                    "version": ["status", "id"],
                    "link": ["rel", "href"],
                }
            }
        }

        content_type = req.best_match_content_type()
        body = (wsgi.Serializer(metadata=metadata).serialize(
            response, content_type))

        response = webob.Response()
        response.content_type = content_type
        response.body = body

        return response


def get_view_builder(req):
    base_url = req.application_url
    return ViewBuilder(base_url)


class ViewBuilder(object):

    def __init__(self, base_url):
        """Object initialization.

        :param base_url: url of the root wsgi application
        """
        self.base_url = base_url

    def build(self, version_data):
        """Generic method used to generate a version entity."""
        version = {
            'id': version_data['id'],
            'status': version_data['status'],
            'links': self._build_links(version_data),
        }

        return version

    def _build_links(self, version_data):
        """Generate a container of links that refer to the provided version."""
        href = self.generate_href(version_data["id"])

        links = [
            {
                'rel': 'self',
                'href': href,
            },
        ]

        return links

    def generate_href(self, version_number):
        """Create an url that refers to a specific version_number."""
        return os.path.join(self.base_url, version_number)