import sys

from hypernet_agentless._i18n import _LE, _

from oslo_concurrency import lockutils
from oslo_log import log as logging
from oslo_utils import importutils

from stevedore import driver


LOG = logging.getLogger(__name__)
SYNCHRONIZED_PREFIX = 'hypernet-'
synchronized = lockutils.synchronized_with_prefix(SYNCHRONIZED_PREFIX)


def load_class_by_alias_or_classname(namespace, name):
    """Load class using stevedore alias or the class name
    Load class using the stevedore driver manager
    :param namespace: namespace where the alias is defined
    :param name: alias or class name of the class to be loaded
    :returns class if calls can be loaded
    :raises ImportError if class cannot be loaded
    """

    if not name:
        LOG.error(_LE("Alias or class name is not set"))
        raise ImportError(_("Class not found."))
    try:
        # Try to resolve class by alias
        mgr = driver.DriverManager(namespace, name)
        class_to_load = mgr.driver
    except RuntimeError:
        e1_info = sys.exc_info()
        # Fallback to class name
        try:
            class_to_load = importutils.import_class(name)
        except (ImportError, ValueError):
            LOG.error(_LE("Error loading class by alias"),
                      exc_info=e1_info)
            LOG.error(_LE("Error loading class by class name"),
                      exc_info=True)
            raise ImportError(_("Class not found."))
    return class_to_load
