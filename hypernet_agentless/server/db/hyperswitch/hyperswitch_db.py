
import sqlalchemy as sa

from sqlalchemy import orm

from hypernet_agentless.server.db import model_base


class HyperSwitch(model_base.BASEV2, model_base.HasId, model_base.HasTenant):
    """Define an hyper switch."""

    name = sa.Column(sa.String(length=255), nullable=True)
    device_id = sa.Column(sa.String(length=255), nullable=True)
    flavor = sa.Column(sa.String(length=255), nullable=True)
    instance_id = sa.Column(sa.String(length=255), nullable=True)
    instance_type = sa.Column(sa.String(length=255), nullable=True)
    mgnt_ip = sa.Column(sa.String(length=64), nullable=True)
    data_ip = sa.Column(sa.String(length=64), nullable=True)


class HyperSwitchVmsIp(model_base.BASEV2):
    """Define an hyper switch VM IP."""

    hyperswitch_id = sa.Column(
        sa.String(length=36),
        sa.ForeignKey('hyperswitchs.id'),
        nullable=False,
        primary_key=True)
    vms_ip = sa.Column(
        sa.String(length=64),
        nullable=False,
        primary_key=True)
    index = sa.Column(sa.Integer(), nullable=False)
    hyperswitch = orm.relationship(
        HyperSwitch,
        backref=orm.backref('vms_ips', cascade='all,delete', lazy='joined'),
        primaryjoin='HyperSwitch.id==HyperSwitchVmsIp.hyperswitch_id')


class ProviderPort(model_base.BASEV2, model_base.HasId, model_base.HasTenant):
    """Define an provider port."""

    device_id = sa.Column(sa.String(length=255), nullable=True)
    name = sa.Column(sa.String(length=255), nullable=True)
    type = sa.Column(sa.String(length=64), nullable=False)
    provider_ip = sa.Column(sa.String(length=64), nullable=False)
    flavor = sa.Column(sa.String(length=255), nullable=True)
    index = sa.Column(sa.Integer(), nullable=False)


class ProviderSubnetPool(model_base.BASEV2,
                         model_base.HasId,
                         model_base.HasTenant):

    cidr = sa.Column(sa.String(64), nullable=False)
