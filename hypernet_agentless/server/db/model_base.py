
from oslo_db.sqlalchemy import models
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy.ext import declarative
from sqlalchemy import orm

from hypernet_agentless.common import hs_constants


class HasTenant(object):
    """Tenant mixin, add to subclasses that have a tenant."""

    # NOTE(jkoelker) tenant_id is just a free form string ;(
    tenant_id = sa.Column(sa.String(hs_constants.TENANT_ID_FIELD_SIZE))


class HasId(object):
    """id mixin, add to subclasses that have an id."""

    id = sa.Column(sa.String(hs_constants.UUID_FIELD_SIZE),
                   primary_key=True,
                   default=uuidutils.generate_uuid)


class HasStatusDescription(object):
    """Status with description mixin."""

    status = sa.Column(sa.String(hs_constants.STATUS_FIELD_SIZE),
                       nullable=False)
    status_description = sa.Column(sa.String(hs_constants.DESCRIPTION_FIELD_SIZE))


class _HypernetBase(models.ModelBase):
    """Base class for Hypernet Models."""

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


class _HypernetBaseV2(_HypernetBase):

    @declarative.declared_attr
    def __tablename__(cls):
        # Use the pluralized name of the class as the table name.
        return cls.__name__.lower() + 's'


BASEV2 = declarative.declarative_base(cls=_HypernetBaseV2)