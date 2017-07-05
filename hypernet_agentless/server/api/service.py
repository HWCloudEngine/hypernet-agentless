
import logging as std_logging

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
from oslo_service import sslutils
from oslo_service import wsgi
from oslo_utils import excutils

from hypernet_agentless._i18n import _
from hypernet_agentless.server import config


LOG = logging.getLogger(__name__)


class WsgiService(service.ServiceBase):
    """Base class for WSGI based services.
    For each api you define, you must also define these flags:
    :<api>_listen: The address on which to listen
    :<api>_listen_port: The port on which to listen
    """

    def __init__(self, app_name):
        self.app_name = app_name
        self.wsgi_app = None

    def start(self):
        self.wsgi_app = _run_wsgi(self.app_name)

    def wait(self):
        if self.wsgi_app:
            self.wsgi_app.wait()

    def stop(self):
        pass

    def reset(self):
        pass


class HypernetApiService(WsgiService):
    """Class for hypernet-api service."""

    @classmethod
    def create(cls, app_name='hypernet'):

        # Dump the initial option values
        cfg.CONF.log_opt_values(LOG, std_logging.DEBUG)
        service = cls(app_name)
        return service


def serve_wsgi(cls):

    try:
        service = cls.create()
    except Exception:
        with excutils.save_and_reraise_exception():
            LOG.exception(_('Unrecoverable error: please check log '
                            'for details.'))

    return service


def _run_wsgi(app_name):
    app = config.load_paste_app(app_name)
    if not app:
        LOG.error(_('No known API applications configured.'))
        return
    server = wsgi.Server(
        cfg.CONF,
        app_name,
        app,
        host=cfg.CONF.bind_host,
        port=cfg.CONF.bind_port,
        use_ssl=sslutils.is_enabled(cfg.CONF)
    )
    server.start()
    # Dump all option values here after all options are parsed
    cfg.CONF.log_opt_values(LOG, std_logging.DEBUG)
    LOG.info(_("Hypernet service started, listening on %(host)s:%(port)s"),
             {'host': cfg.CONF.bind_host,
              'port': cfg.CONF.bind_port})
    return server
