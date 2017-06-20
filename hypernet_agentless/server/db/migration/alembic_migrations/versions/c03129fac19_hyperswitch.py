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

Revision ID: c03129fac19
Revises: start_hypernet_agentless
Create Date: 2017-01-30 16:21:45.593104

"""

# revision identifiers, used by Alembic.
revision = 'c03129fac19'
down_revision = 'start_hypernet_agentless'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'hyperswitchs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('device_id', sa.String(length=255), nullable=True),
        sa.Column('flavor', sa.String(length=255), nullable=True),
        sa.Column('instance_id', sa.String(length=255), nullable=True),
        sa.Column('instance_type', sa.String(length=255), nullable=True),
        sa.Column('mgnt_ip', sa.String(length=64), nullable=True),
        sa.Column('data_ip', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id'))

    op.create_table(
        'hyperswitchvmsips',
        sa.Column('hyperswitch_id',
                  sa.String(length=36),
                  nullable=False,
                  primary_key=True),
        sa.Column('vms_ip',
                  sa.String(length=64),
                  nullable=False,
                  primary_key=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['hyperswitch_id'],
            ['hyperswitchs.id'],
            ondelete='CASCADE'),
    )
