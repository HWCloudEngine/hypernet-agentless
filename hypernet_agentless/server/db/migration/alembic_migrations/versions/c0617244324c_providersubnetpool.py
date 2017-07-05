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

Revision ID: c0617244324c
Revises: 490c90d35219
Create Date: 2017-07-06 08:39:40.305851

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0617244324c'
down_revision = '490c90d35219'


def upgrade():
    op.create_table(
        'providersubnetpools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('cidr', sa.String(64), nullable=False),
        sa.Column('used_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'))
