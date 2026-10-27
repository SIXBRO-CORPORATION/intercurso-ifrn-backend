"""v20

Revision ID: 877d64f735c4
Revises: 51540a8efbe2
Create Date: 2026-10-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '877d64f735c4'
down_revision: Union[str, Sequence[str], None] = '51540a8efbe2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Infraestrutura de Push Notification (UC016, Fluxo Alternativo 2; ADR 0005):
    tabela de tokens de dispositivo (FCM) usados para envio de push a Alunos
    autenticados. `active=False` cobre tanto opt-out (logout) quanto
    invalidação do token pelo provedor.
    """
    op.create_table(
        'device_tokens',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.String(length=10), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_device_tokens_user_id'), 'device_tokens', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_device_tokens_token'), 'device_tokens', ['token'], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_device_tokens_token'), table_name='device_tokens')
    op.drop_index(op.f('ix_device_tokens_user_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
