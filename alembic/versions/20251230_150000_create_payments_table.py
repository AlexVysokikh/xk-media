"""create payments table

Revision ID: 001
Revises: 
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('pending', 'waiting', 'succeeded', 'canceled', 'failed', name='paymentstatus'), nullable=False),
        sa.Column('pk_invoice_id', sa.String(length=100), nullable=True),
        sa.Column('pay_url', sa.String(length=500), nullable=True),
        sa.Column('pk_payment_id', sa.String(length=100), nullable=True),
        sa.Column('pk_ps_id', sa.String(length=100), nullable=True),
        sa.Column('raw_notify', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_pk_invoice_id'), 'payments', ['pk_invoice_id'], unique=False)
    op.create_index(op.f('ix_payments_pk_payment_id'), 'payments', ['pk_payment_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_pk_payment_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_pk_invoice_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.execute('DROP TYPE IF EXISTS paymentstatus')


