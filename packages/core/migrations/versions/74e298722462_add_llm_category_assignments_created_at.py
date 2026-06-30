"""add_llm_category_assignments_created_at

Revision ID: 74e298722462
Revises: 2814a2ef2031
Create Date: 2026-06-30 11:49:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


revision: str = '74e298722462'
down_revision: Union[str, Sequence[str], None] = '2814a2ef2031'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("llm_category_assignments")]
    if "created_at" not in cols:
        # SQLite does not support ALTER TABLE ADD with function defaults.
        # We use the text type to avoid server_default for the migration,
        # then set existing rows via UPDATE.
        op.add_column("llm_category_assignments", sa.Column("created_at", sa.DateTime(), nullable=True))
        op.execute("UPDATE llm_category_assignments SET created_at = datetime('now') WHERE created_at IS NULL")


def downgrade() -> None:
    op.drop_column("llm_category_assignments", "created_at")
