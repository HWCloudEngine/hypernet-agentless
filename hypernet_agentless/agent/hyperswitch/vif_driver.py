
import abc
import six


@six.add_metaclass(abc.ABCMeta)
class HyperVIFDriver(object):

    @abc.abstractmethod
    def startup_init(self):
        pass

    @abc.abstractmethod
    def cleanup(self):
        pass

    @abc.abstractmethod
    def plug(self, device_id, vif_id, mac):
        pass

    @abc.abstractmethod
    def unplug(self, vif_id):
        pass
