'''
Created on Apr 18, 2017

@author: avig
'''
 
import sqlalchemy as sa

from sqlalchemy import orm

from hypernet_agentless.server.db import model_base


class DNS_Domain(model_base.BASEV1, model_base.HasId, model_base.HasTenant):
    __tablename__ = 'domains'
    name = sa.Column(sa.String(length=255), nullable=True)
    master = sa.Column(sa.String(length=128), nullable=True)
    last_check = sa.Column(sa.Integer(), nullable=True)
    type = sa.Column(sa.String(length=6), nullable=True)
    notified_serial = sa.Column(sa.Integer(), nullable=True)
    account = sa.Column(sa.String(length=40), nullable=True)


class DNS_Record(model_base.BASEV1, model_base.HasId, model_base.HasTenant):
    __tablename__ = 'records'
    domain_id = sa.Column(sa.String(length=36), nullable=True)
    name = sa.Column(sa.String(length=255), nullable=True)
    type = sa.Column(sa.String(length=10), nullable=True)
    content = sa.Column(sa.String(length=255), nullable=True)
    ttl = sa.Column(sa.Integer(), nullable=True)
    prio = sa.Column(sa.Integer(), nullable=True)
    change_date = sa.Column(sa.Integer(), nullable=True)
    disabled = sa.Column(sa.Integer(), nullable=True)
    ordername = sa.Column(sa.String(length=255), nullable=True)
    auth = sa.Column(sa.Integer(), nullable=True)
    discriminator = sa.Column(sa.String(length=255), nullable=True)
    hs_id = sa.Column(sa.String(length=255), nullable=True)
    net_index = sa.Column(sa.Integer(), nullable=True)


class HS_Data(model_base.BASEV1, model_base.HasId, model_base.HasTenant):
    __tablename__ = 'hs_data'
    hs_id = sa.Column(sa.String(length=255), nullable=True)
    net_index = sa.Column(sa.Integer(), nullable=True)
    ip = sa.Column(sa.String(length=255), nullable=True)
    
    

if __name__ == '__main__':
    pass
 
 
