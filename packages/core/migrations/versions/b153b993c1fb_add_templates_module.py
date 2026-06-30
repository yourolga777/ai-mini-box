"""add_templates_module

Revision ID: b153b993c1fb
Revises: b2c3d4e5f6a7
Create Date: 2026-06-29 15:25:20.492843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b153b993c1fb'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'templates' not in tables:
        op.create_table('templates',
            sa.Column('id', sa.String(length=32), nullable=False),
            sa.Column('scope', sa.String(length=20), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('variables', sa.Text(), nullable=True),
            sa.Column('defaults', sa.Text(), nullable=True),
            sa.Column('triggers', sa.Text(), nullable=True),
            sa.Column('confidence_min', sa.Float(), nullable=True),
            sa.Column('usage_count', sa.Integer(), nullable=True),
            sa.Column('success_count', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Integer(), nullable=True),
            sa.Column('is_archived', sa.Integer(), nullable=True),
            sa.Column('created_by_id', sa.String(length=32), nullable=True),
            sa.Column('updated_by_id', sa.String(length=32), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('scope', 'slug', name='uq_templates_scope_slug'),
        )
        op.create_index('idx_templates_scope_category_active', 'templates', ['scope', 'category', 'is_active'])

    if 'training_log' not in tables:
        op.create_table('training_log',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('message_text', sa.Text(), nullable=False),
            sa.Column('category_predicted', sa.String(length=50), nullable=True),
            sa.Column('category_corrected', sa.String(length=50), nullable=True),
            sa.Column('is_order_predicted', sa.Boolean(), nullable=True),
            sa.Column('is_order_corrected', sa.Boolean(), nullable=True),
            sa.Column('template_id_used', sa.String(length=32), nullable=True),
            sa.Column('operator_approved', sa.Boolean(), nullable=True),
            sa.Column('operator_edited', sa.Boolean(), nullable=True),
            sa.Column('final_reply_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'template_usage_log' not in tables:
        op.create_table('template_usage_log',
            sa.Column('id', sa.String(length=32), nullable=False),
            sa.Column('template_id', sa.String(length=32), nullable=False),
            sa.Column('message_id', sa.String(length=32), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('was_used', sa.Integer(), nullable=True),
            sa.Column('operator_approved', sa.Integer(), nullable=True),
            sa.Column('operator_edited', sa.Integer(), nullable=True),
            sa.Column('final_text', sa.Text(), nullable=True),
            sa.Column('response_time_ms', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_usage_log_template_id', 'template_usage_log', ['template_id'])
        op.create_index('idx_usage_log_created_at', 'template_usage_log', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_usage_log_created_at', table_name='template_usage_log')
    op.drop_index('idx_usage_log_template_id', table_name='template_usage_log')
    op.drop_index('idx_templates_scope_category_active', table_name='templates')
    op.drop_table('template_usage_log')
    op.drop_table('training_log')
    op.drop_table('templates')
