"""add_llm_categories_order

Revision ID: 2814a2ef2031
Revises: b153b993c1fb
Create Date: 2026-06-30 10:46:23.486944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2814a2ef2031'
down_revision: Union[str, Sequence[str], None] = 'b153b993c1fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # add order column to llm_categories
    cat_cols = [c["name"] for c in inspector.get_columns("llm_categories")]
    if "order" not in cat_cols:
        op.add_column("llm_categories", sa.Column("order", sa.Integer(), server_default="0"))

    # add created_at column to llm_category_assignments
    asgn_cols = [c["name"] for c in inspector.get_columns("llm_category_assignments")]
    if "created_at" not in asgn_cols:
        op.add_column("llm_category_assignments", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))


def downgrade() -> None:
    op.drop_column("llm_category_assignments", "created_at")
    op.drop_column("llm_categories", "order")
