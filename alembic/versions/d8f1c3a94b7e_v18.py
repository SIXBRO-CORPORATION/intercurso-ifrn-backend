"""v18

Revision ID: d8f1c3a94b7e
Revises: abb49402efbd
Create Date: 2026-10-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8f1c3a94b7e'
down_revision: Union[str, Sequence[str], None] = 'abb49402efbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    A decisão de ter ou não "partida de 3º lugar" deixa de ser uma
    característica fixa da modalidade (`modality_configurations.
    has_third_place_match`) e passa a ser escolhida pelo monitor na hora de
    criar o chaveamento (UC011), junto das demais opções de `configuration`
    (igual `num_groups`, `rounds`, `double_round` etc.), com default True
    sugerido automaticamente. Ver `business/bracket/engine/config_suggester.py`
    e `business/bracket/engine/draw_engine.py`.
    """
    op.drop_column('modality_configurations', 'has_third_place_match')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'modality_configurations',
        sa.Column(
            'has_third_place_match',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
