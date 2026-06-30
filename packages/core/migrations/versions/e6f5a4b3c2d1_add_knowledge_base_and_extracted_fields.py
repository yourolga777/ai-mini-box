"""add_knowledge_base_and_extracted_fields

Revision ID: e6f5a4b3c2d1
Revises: d9a1b2c3e4f5
Create Date: 2026-06-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e6f5a4b3c2d1'
down_revision: Union[str, Sequence[str], None] = 'd9a1b2c3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'knowledge_base' not in inspector.get_table_names():
        op.create_table('knowledge_base',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('topic', sa.Enum('PRICES', 'ORDER', 'COMPLAINT', 'SCHEDULE', 'OTHER', name='topic'), nullable=True),
            sa.Column('question_keywords', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('answer_text', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    msg_cols = [c["name"] for c in inspector.get_columns("messages")]
    if "extracted_phone" not in msg_cols:
        op.add_column('messages', sa.Column('extracted_phone', sa.String(50), nullable=True))
    if "extracted_name" not in msg_cols:
        op.add_column('messages', sa.Column('extracted_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'extracted_name')
    op.drop_column('messages', 'extracted_phone')
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'knowledge_base' in inspector.get_table_names():
        op.drop_table('knowledge_base')
