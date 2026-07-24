"""add logs table (audit)

Revision ID: c1a9d3f7e001
Revises: b5886801e33d
Create Date: 2026-07-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1a9d3f7e001'
down_revision: Union[str, Sequence[str], None] = 'b5886801e33d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('actor_role', sa.String(length=20), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_logs_actor_id'), 'logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_logs_action'), 'logs', ['action'], unique=False)
    op.create_index(op.f('ix_logs_created_at'), 'logs', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_logs_created_at'), table_name='logs')
    op.drop_index(op.f('ix_logs_action'), table_name='logs')
    op.drop_index(op.f('ix_logs_actor_id'), table_name='logs')
    op.drop_table('logs')