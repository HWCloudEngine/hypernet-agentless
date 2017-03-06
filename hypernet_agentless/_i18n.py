from oslo_i18n import _factory

DOMAIN = 'hypernet_agentless'

# Create the global translation functions.
_translators = _factory.TranslatorFactory(DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary

_LI = _translators.log_info
_LW = _translators.log_warning
_LE = _translators.log_error
_LC = _translators.log_critical
