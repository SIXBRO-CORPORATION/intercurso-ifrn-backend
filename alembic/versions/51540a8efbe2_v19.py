"""v19

Revision ID: 51540a8efbe2
Revises: d8f1c3a94b7e
Create Date: 2026-10-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '51540a8efbe2'
down_revision: Union[str, Sequence[str], None] = 'd8f1c3a94b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    RN confirmada em docs/qa/a04-minhas-equipes-criar-equipe.md (Fase 1,
    achado #8): o nome de uma equipe deve ser único dentro da mesma
    modalidade e temporada (o mesmo nome pode se repetir em outra
    modalidade, ou na mesma modalidade em outra temporada). Antes não havia
    nenhuma restrição de unicidade de nome na tabela `teams`.
    """
    op.create_index(
        "uq_teams_name_modality_season",
        "teams",
        ["name", "modality_id", "season_id"],
        unique=True,
        postgresql_where=text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_teams_name_modality_season", table_name="teams")
