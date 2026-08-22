"""v11

Revision ID: 3fbd6f2e9a41
Revises: 08134248a8f8
Create Date: 2026-08-21 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fbd6f2e9a41'
down_revision: Union[str, Sequence[str], None] = '08134248a8f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    UC015 (Finalizar Partida) - Fluxo Alternativo 1: disputa de pênaltis.
    `penalty_shootout_active` controla se a partida está na interface
    simplificada de cobrança-a-cobrança; os contadores de pênaltis ficam
    separados do placar oficial (team1_score/team2_score), que nunca é
    alterado pela disputa (RN19-20).
    """
    op.add_column(
        'matches',
        sa.Column(
            'penalty_shootout_active', sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column('matches', sa.Column('team1_penalty_score', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('team2_penalty_score', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('matches', 'team2_penalty_score')
    op.drop_column('matches', 'team1_penalty_score')
    op.drop_column('matches', 'penalty_shootout_active')
