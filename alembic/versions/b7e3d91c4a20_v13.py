"""v13

Regra de negócio: apenas uma temporada ativa por vez (UC001 regra 10).

1. Rascunhos e temporadas finalizadas não podem estar ativos. Dados gerados pelo
   bug em que toda temporada nascia com `active = true` são corrigidos aqui.
2. Se ainda houver mais de uma temporada ativa, mantém a de maior prioridade
   (em andamento antes de inscrições abertas, depois a mais recente) e desativa
   as demais.
3. Índice único parcial sobre `active`, garantindo no banco que nunca existam
   duas temporadas ativas não removidas.

Revision ID: b7e3d91c4a20
Revises: a1c017f00d17
Create Date: 2026-10-04 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "b7e3d91c4a20"
down_revision: Union[str, Sequence[str], None] = "a1c017f00d17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_index(
        "uq_seasons_single_active",
        "seasons",
        ["active"],
        unique=True,
        postgresql_where=text("active = true AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_seasons_single_active", table_name="seasons")
