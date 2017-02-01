
import sqlalchemy as sa

from neutron.db import model_base
from neutron.db import models_v2

from sqlalchemy import orm

class HyperSwitch(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    """Define an hyper switch."""

    device_id = sa.Column(sa.String(length=255), nullable=True)
    flavor = sa.Column(sa.String(length=255), nullable=True)
    instance_id = sa.Column(sa.String(length=255), nullable=True),
    instance_type = sa.Column(sa.String(length=255), nullable=True),
    mgnt_ip = sa.Column(sa.String(length=64), nullable=True),
    data_ip = sa.Column(sa.String(length=64), nullable=True),


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


class AgentlessPort(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    """Define an agentless port."""

    device_id = sa.Column(sa.String(length=255), nullable=True)
    name = sa.Column(sa.String(length=255), nullable=True)
    provider_ip = sa.Column(sa.String(length=64), nullable=False)
    flavor = sa.Column(sa.String(length=255), nullable=True)
    index = sa.Column(sa.Integer(), nullable=False)