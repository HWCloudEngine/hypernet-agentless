
import routes as routes_mapper
from six import iteritems
import urlparse
import webob.dec

from hypernet_agentless.server.api import extensions
from hypernet_agentless.server.api import wsgi
from hypernet_agentless.server.api.v1 import attributes


class Index(wsgi.Application):
    def __init__(self, resources):
        self.resources = resources

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        metadata = {}

        layout = []
        for name, collection in iteritems(self.resources):
            href = urlparse.urljoin(req.path_url, collection)
            resource = {'name': name,
                        'collection': collection,
                        'links': [{'rel': 'self',
                                   'href': href}]}
            layout.append(resource)
        response = dict(resources=layout)
        content_type = req.best_match_content_type()
        body = wsgi.Serializer(metadata=metadata).serialize(response,
                                                            content_type)
        return webob.Response(body=body, content_type=content_type)


class APIRouter(wsgi.Router):

    @classmethod
    def factory(cls, global_config, **local_config):
        return cls(**local_config)

    def __init__(self, **local_config):
        mapper = routes_mapper.Mapper()
        ext_mgr = extensions.ExtensionManager.get_instance()
        ext_mgr.extend_resources('1.0', attributes.RESOURCE_ATTRIBUTE_MAP)
        super(APIRouter, self).__init__(mapper)