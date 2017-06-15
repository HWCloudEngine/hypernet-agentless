# Copyright 2017 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""empty message

Revision ID: d76f8fb8ba0f
Revises: 490c90d35219
Create Date: 2017-06-14 16:49:51.997839

"""

# revision identifiers, used by Alembic.
revision = 'd76f8fb8ba0f'
down_revision = '490c90d35219'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.create_table(
        'domains',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('master', sa.String(length=128), nullable=True),
        sa.Column('last_check', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=6), nullable=True),
        sa.Column('notified_serial', sa.Integer(), nullable=True),
        sa.Column('account', sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    
    op.create_table(
        'records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('domain_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=10), nullable=True),
        sa.Column('content', sa.String(length=255), nullable=True),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.Column('prio', sa.Integer(), nullable=True),
        sa.Column('change_date', sa.Integer(), nullable=True),
        sa.Column('disabled', sa.Integer(), nullable=True),
        sa.Column('ordername', sa.String(length=255), nullable=True),
        sa.Column('auth', sa.Integer(), nullable=True),
        sa.Column('discriminator', sa.String(length=255), nullable=True),
        sa.Column('hs_id', sa.String(length=255), nullable=True),
        sa.Column('net_index', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    
    op.create_table(
        'hs_data',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('hs_id', sa.String(length=255), nullable=True),
        sa.Column('net_index', sa.Integer(), nullable=True),
        sa.Column('ip',sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'))

