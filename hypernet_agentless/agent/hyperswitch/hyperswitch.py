import eventlet
eventlet.monkey_patch()

import sys

from oslo import messaging

from hypernet_agentless.agent.hyperswitch import config
from hypernet_agentless.agent.hyperswitch import vif_hyperswitch_driver

from oslo.config import cfg

from neutron.openstack.common import log as logging

from neutron import context
from neutron.common import rpc
from neutron.openstack.common.gettextutils import _LI


LOG = logging.getLogger(__name__)


class HyperSwitchAgentCallback(object):
    """Processes the rpc call back."""

    RPC_API_VERSION = '1.0'

    def __init__(self):
        target = messaging.Target(topic='hyperswitch-callback',
                                  version='1.0',
                                  exchange='hyperswitch')
        self.client = rpc.get_client(target)
        self.context = context.get_admin_context()
        super(HyperSwitchAgentCallback, self).__init__()

    def get_vif_for_provider_ip(self, provider_ip, host_id, evt):
        """Retrieve the VIFs for a provider IP."""
        return self.client.call(self.context, 'get_vif_for_provider_ip',
                                provider_ip=provider_ip,
                                host_id=host_id,
                                evt=evt)


class HyperSwitchAgent(object):

    def __init__(self):
        super(HyperSwitchAgent, self).__init__()
        self.device_id = cfg.CONF.host

        # the queue client for plug/unplug calls from nova driver
        endpoints = [self]
        target = messaging.Target(topic='hyperswitch-update',
                                  version='1.0',
                                  exchange='hyperswitch',
                                  server=cfg.CONF.host)
        self.server = rpc.get_server(target, endpoints)

        # the call back to nova driver init
        self.call_back = HyperSwitchAgentCallback()

        # instance according to configuration
        self.vif_driver = vif_hyperswitch_driver.HyperSwitchVIFDriver(
            device_id=self.device_id,
            call_back=self.call_back)

        self.vif_driver.startup_init()

        self.server.start()

    def daemon_loop(self):
        while True:
            eventlet.sleep(600)


def main():
    config.init(sys.argv[1:])

    agent = HyperSwitchAgent()
    # Start everything.
    LOG.info(_LI("Agent initialized successfully, now running. "))
    agent.daemon_loop()


if __name__ == "__main__":
    main()
