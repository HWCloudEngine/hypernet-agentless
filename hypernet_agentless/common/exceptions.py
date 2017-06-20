"""
Hypernet base exception handling.
"""

from oslo_utils import excutils

from hypernet_agentless._i18n import _


class HypernetException(Exception):
    """Base Hypernet Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred."

    def __init__(self, **kwargs):
        try:
            super(HypernetException, self).__init__(self.message % kwargs)
            self.msg = self.message % kwargs
        except Exception:
            with excutils.save_and_reraise_exception() as ctxt:
                if not self.use_fatal_exceptions():
                    ctxt.reraise = False
                    # at least get the core message out if something happened
                    super(HypernetException, self).__init__(self.message)

    def __unicode__(self):
        return unicode(self.msg)

    def use_fatal_exceptions(self):
        return False


class NotFound(HypernetException):
    """A generic not found exception."""
    pass


class Conflict(HypernetException):
    """A generic conflict exception."""
    pass


class NotAuthorized(HypernetException):
    """A generic not authorized exception."""
    message = _("Not authorized.")


class InvalidContentType(HypernetException):
    message = "Invalid content type %(content_type)s"


class BadRequest(HypernetException):
    message = 'Bad %(resource)s request: %(msg)s'


class ExtensionsNotFound(HypernetException):
    message = _("Extensions not found: %(extensions)s.")


class DuplicatedExtension(HypernetException):
    message = _("Found duplicate extension: %(alias)s.")


class MalformedRequestBody(BadRequest):
    message = "Malformed request body: %(reason)s"


class RetryRequest(Exception):
    """Error raised when DB operation needs to be retried.

    That could be intentionally raised by the code without any real DB errors.
    """
    def __init__(self, inner_exc):
        self.inner_exc = inner_exc


class InvalidInput(BadRequest):
    """A bad request due to invalid input.
    A specialization of the BadRequest error indicating bad input was
    specified.
    :param error_message: Details on the operation that failed due to bad
    input.
    """
    message = _("Invalid input for operation: %(error_message)s.")


class PolicyInitError(HypernetException):
    message = _("Failed to init policy %(policy)s because %(reason)s")


class PolicyCheckError(HypernetException):
    message = _("Failed to check policy %(policy)s because %(reason)s")


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class Invalid(HypernetException):
    def __init__(self, message=None):
        self.message = message
        super(Invalid, self).__init__()


class InUse(HypernetException):
    message = _("The resource is inuse")


class ServiceUnavailable(HypernetException):
    message = _("The service is unavailable")
