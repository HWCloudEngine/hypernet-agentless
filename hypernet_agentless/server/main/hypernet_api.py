
import sys

import eventlet
eventlet.monkey_patch()
from oslo_config import cfg
import oslo_i18n
from oslo_service import service

from hypernet_agentless._i18n import _
from hypernet_agentless.server import config
from hypernet_agentless.server.api import service as h_service

oslo_i18n.install('hypernet')


def main():
    # the configuration will be read into the cfg.CONF global data structure
    config.init(sys.argv[1:])
    if not cfg.CONF.config_file:
        sys.exit(_(
            "ERROR: Unable to find configuration file via the default"
            " search paths (~/.hypernet/, ~/, /etc/hypernet/, /etc/) and"
            " the '--config-file' option!"))

    try:
        hypernet_api = h_service.serve_wsgi(h_service.HypernetApiService)
        launcher = service.launch(cfg.CONF, hypernet_api,
                                  workers=cfg.CONF.api_workers or None)
        launcher.wait()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        sys.exit(_("ERROR: %s") % e)


if __name__ == "__main__":
    main()