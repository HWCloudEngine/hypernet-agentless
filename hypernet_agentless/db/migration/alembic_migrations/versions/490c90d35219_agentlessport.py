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

Revision ID: 490c90d35219
Revises: c03129fac19
Create Date: 2017-01-31 08:54:13.511188

"""

# revision identifiers, used by Alembic.
revision = '490c90d35219'
down_revision = 'c03129fac19'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.create_table(
        'agentlessports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('provider_ip', sa.String(length=64), nullable=False),
        sa.Column('flavor', sa.String(length=255), nullable=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('agentlessports')
