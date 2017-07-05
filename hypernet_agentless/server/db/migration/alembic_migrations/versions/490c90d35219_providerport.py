"""empty message

Revision ID: 490c90d35219
Revises: c03129fac19
Create Date: 2017-01-31 08:54:13.511188

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '490c90d35219'
down_revision = 'c03129fac19'


def upgrade():
    op.create_table(
        'providerports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('provider_ip', sa.String(length=64), nullable=False),
        sa.Column('flavor', sa.String(length=255), nullable=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'))
