"""add_extracted_order_id

Revision ID: f7a8b9c0d1e2
Revises: e6f5a4b3c2d1
Create Date: 2026-06-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f5a4b3c2d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("messages")]
    if "extracted_order_id" not in cols:
        with op.batch_alter_table('messages') as batch_op:
            batch_op.add_column(sa.Column('extracted_order_id', sa.Integer(), sa.ForeignKey('orders.id', name='fk_messages_extracted_order_id'), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('messages') as batch_op:
        batch_op.drop_column('extracted_order_id')
