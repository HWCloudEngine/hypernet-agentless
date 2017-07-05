import sys

from hypernet_agentless.agent.hyperswitch import config
from hypernet_agentless.agent.hyperswitch import vif_hyperswitch_driver


def main():
    config.init(sys.argv[1:])
    vif_driver = vif_hyperswitch_driver.HyperSwitchVIFDriver()
    vif_driver.cleanup()


if __name__ == "__main__":
    main()
