"""add_tasks_table

Revision ID: d9a1b2c3e4f5
Revises: ab2eb6df34f5
Create Date: 2026-06-23 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd9a1b2c3e4f5'
down_revision: Union[str, Sequence[str], None] = 'ab2eb6df34f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'tasks' not in inspector.get_table_names():
        op.create_table('tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('due_time', sa.String(length=5), nullable=True),
        sa.Column('priority',
            sa.Enum('LOW', 'MEDIUM', 'HIGH', name='taskpriority'),
            nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(),
            server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(),
            server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tasks')
    op.execute('DROP TYPE IF EXISTS taskpriority')
