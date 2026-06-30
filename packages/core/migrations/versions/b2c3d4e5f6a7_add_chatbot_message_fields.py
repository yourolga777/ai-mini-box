"""add_chatbot_message_fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("messages")}

    if "category" not in existing:
        op.add_column("messages", sa.Column("category", sa.String(50), nullable=True))
    if "subcategory" not in existing:
        op.add_column("messages", sa.Column("subcategory", sa.String(100), nullable=True))
    if "need_human" not in existing:
        op.add_column("messages", sa.Column("need_human", sa.Boolean(), server_default="0"))
    if "auto_replied" not in existing:
        op.add_column("messages", sa.Column("auto_replied", sa.Boolean(), server_default="0"))
    if "auto_reply_text" not in existing:
        op.add_column("messages", sa.Column("auto_reply_text", sa.Text(), nullable=True))
    if "operator_context" not in existing:
        op.add_column("messages", sa.Column("operator_context", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("messages")}

    for col in ("operator_context", "auto_reply_text", "auto_replied", "need_human", "subcategory", "category"):
        if col in existing:
            op.drop_column("messages", col)
