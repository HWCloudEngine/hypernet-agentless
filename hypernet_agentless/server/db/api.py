
from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade


context_manager = enginefacade.transaction_context()

_FACADE = None


def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        context_manager.configure(sqlite_fk=True, **cfg.CONF.database)
        _FACADE = context_manager._factory.get_legacy_facade()

    return _FACADE


def get_engine():
    """Helper method to grab engine."""
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(autocommit=True, expire_on_commit=False):
    """Helper method to grab session."""
    facade = _create_facade_lazily()
    return facade.get_session(autocommit=autocommit,
                              expire_on_commit=expire_on_commit)
