"""v10

Revision ID: 08134248a8f8
Revises: da083ec37273
Create Date: 2026-08-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08134248a8f8'
down_revision: Union[str, Sequence[str], None] = 'da083ec37273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    UC015 (Finalizar Partida) - avanço automático no chaveamento: adiciona a
    coluna auto-referenciada `next_match_id`, que aponta para a partida da
    próxima fase que deve receber o time vencedor (estratégia com
    persistência, decidida para a Fase 5 - ver docs/ai/planejamento.md).
    """
    op.add_column('matches', sa.Column('next_match_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_matches_next_match_id', 'matches', 'matches', ['next_match_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_matches_next_match_id', 'matches', type_='foreignkey')
    op.drop_column('matches', 'next_match_id')
