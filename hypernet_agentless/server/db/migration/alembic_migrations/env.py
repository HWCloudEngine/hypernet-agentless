from logging import config as logging_config

from alembic import context

from oslo_config import cfg
from oslo_db.sqlalchemy import models
from oslo_db.sqlalchemy import session

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy.ext import declarative


MYSQL_ENGINE = None
AGENTLESS_VERSION_TABLE = 'agentless_alembic_version'
config = context.config
hypernet_config = config.hypernet_config
logging_config.fileConfig(config.config_file_name)


class _HypernetBase(models.ModelBase):
    """Base class for Neutron Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __iter__(self):
        self._i = iter(orm.object_mapper(self).columns)
        return self

    def next(self):
        n = next(self._i).name
        return n, getattr(self, n)

    __next__ = next

    def __repr__(self):
        """sqlalchemy based automatic __repr__ method."""
        items = ['%s=%r' % (col.name, getattr(self, col.name))
                 for col in self.__table__.columns]
        return "<%s.%s[object at %x] {%s}>" % (self.__class__.__module__,
                                               self.__class__.__name__,
                                               id(self), ', '.join(items))


class HypernetBaseV2(_HypernetBase):

    @declarative.declared_attr
    def __tablename__(cls):
        # Use the pluralized name of the class as the table name.
        return cls.__name__.lower() + 's'


target_metadata = declarative.declarative_base(cls=HypernetBaseV2)


def set_mysql_engine():
    try:
        mysql_engine = hypernet_config.command.mysql_engine
    except cfg.NoSuchOptError:
        mysql_engine = None

    global MYSQL_ENGINE
    MYSQL_ENGINE = (mysql_engine or
                    target_metadata.__table_args__['mysql_engine'])


def run_migrations_offline():
    set_mysql_engine()

    kwargs = dict()
    if hypernet_config.database.connection:
        kwargs['url'] = hypernet_config.database.connection
    else:
        kwargs['dialect_name'] = hypernet_config.database.engine
    kwargs['version_table'] = AGENTLESS_VERSION_TABLE
    context.configure(**kwargs)

    with context.begin_transaction():
        context.run_migrations()


@event.listens_for(sa.Table, 'after_parent_attach')
def set_storage_engine(target, parent):
    if MYSQL_ENGINE:
        target.kwargs['mysql_engine'] = MYSQL_ENGINE


def run_migrations_online():
    set_mysql_engine()
    engine = session.create_engine(hypernet_config.database.connection)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=AGENTLESS_VERSION_TABLE
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()