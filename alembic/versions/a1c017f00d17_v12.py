"""v12

UC017 - Corrigir Eventos da Partida.

`match_sets` já possuía `deleted_at`/`active` (herdados de AbstractEntity)
desde a v6, então não é necessária nenhuma coluna nova. O que muda aqui é
puramente a regra de mutabilidade da tabela (ver decisão 2/3 do handoff do
UC017 e ADR002, seção "Momento 5"):

1. A UniqueConstraint simples `uq_match_sets_match_id_set_number` é
   substituída por um índice único parcial `WHERE deleted_at IS NULL`, para
   permitir que uma linha antiga seja soft-deletada e uma nova linha correta
   seja inserida para o mesmo (match_id, set_number) sem violar unicidade.
2. A trigger `prevent_match_sets_mutation()` é reescrita para permitir
   apenas a transição de soft delete (`deleted_at` NULL -> NOT NULL, sem
   nenhuma outra coluna de negócio mudando). DELETE/TRUNCATE continuam
   bloqueados sempre, como antes.

`match_events` não precisa de migration: já tinha `deleted_at` desde a v1 e
o adapter (`MatchEventRepositoryAdapter.soft_delete_event`) já sabia usá-lo.

Revision ID: a1c017f00d17
Revises: 3fbd6f2e9a41
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from alembic_utils.pg_function import PGFunction
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'a1c017f00d17'
down_revision: Union[str, Sequence[str], None] = '3fbd6f2e9a41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_prevent_match_sets_mutation = PGFunction(
    schema="public",
    signature="prevent_match_sets_mutation()",
    definition=(
        "RETURNS trigger AS $$\n"
        "    BEGIN\n"
        "        IF TG_OP = 'TRUNCATE' THEN\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: TRUNCATE is not allowed'\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        IF TG_OP = 'DELETE' THEN\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: DELETE is not allowed (id=%)',\n"
        "                OLD.id\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        IF TG_OP = 'UPDATE' THEN\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: UPDATE is not allowed (id=%)',\n"
        "                OLD.id\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        RETURN NULL;\n"
        "    END;\n"
        "    $$ LANGUAGE plpgsql"
    ),
)

new_prevent_match_sets_mutation = PGFunction(
    schema="public",
    signature="prevent_match_sets_mutation()",
    definition=(
        "RETURNS trigger AS $$\n"
        "    BEGIN\n"
        "        IF TG_OP = 'TRUNCATE' THEN\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: TRUNCATE is not allowed'\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        IF TG_OP = 'DELETE' THEN\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: DELETE is not allowed (id=%)',\n"
        "                OLD.id\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        IF TG_OP = 'UPDATE' THEN\n"
        "            IF OLD.deleted_at IS NULL\n"
        "                AND NEW.deleted_at IS NOT NULL\n"
        "                AND NEW.match_id IS NOT DISTINCT FROM OLD.match_id\n"
        "                AND NEW.set_number IS NOT DISTINCT FROM OLD.set_number\n"
        "                AND NEW.team1_points IS NOT DISTINCT FROM OLD.team1_points\n"
        "                AND NEW.team2_points IS NOT DISTINCT FROM OLD.team2_points\n"
        "                AND NEW.winner_team_id IS NOT DISTINCT FROM OLD.winner_team_id\n"
        "                AND NEW.created_at IS NOT DISTINCT FROM OLD.created_at\n"
        "                AND NEW.active IS NOT DISTINCT FROM OLD.active\n"
        "            THEN\n"
        "                RETURN NEW;\n"
        "            END IF;\n"
        "\n"
        "            RAISE EXCEPTION\n"
        "                'match_sets is immutable\\: only a soft-delete transition '\n"
        "                '(deleted_at NULL -> NOT NULL, no other column change) is '\n"
        "                'allowed (id=%)',\n"
        "                OLD.id\n"
        "                USING ERRCODE = '23000';\n"
        "        END IF;\n"
        "\n"
        "        RETURN NULL;\n"
        "    END;\n"
        "    $$ LANGUAGE plpgsql"
    ),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "uq_match_sets_match_id_set_number", "match_sets", type_="unique"
    )
    op.create_index(
        "uq_match_sets_match_id_set_number",
        "match_sets",
        ["match_id", "set_number"],
        unique=True,
        postgresql_where=text("deleted_at IS NULL"),
    )

    op.replace_entity(new_prevent_match_sets_mutation)


def downgrade() -> None:
    """Downgrade schema."""
    op.replace_entity(old_prevent_match_sets_mutation)

    op.drop_index("uq_match_sets_match_id_set_number", table_name="match_sets")
    op.create_unique_constraint(
        "uq_match_sets_match_id_set_number", "match_sets", ["match_id", "set_number"]
    )
