"""add user secondary_role for dual roles (advertiser + venue)

Revision ID: 002
Revises: 001
Create Date: 2026-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('secondary_role', sa.String(length=20), nullable=True))
    op.create_index(op.f('ix_users_secondary_role'), 'users', ['secondary_role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_secondary_role'), table_name='users')
    op.drop_column('users', 'secondary_role')
