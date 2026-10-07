"""v17

Revision ID: abb49402efbd
Revises: a7c2e5f91b36
Create Date: 2026-10-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abb49402efbd'
down_revision: Union[str, Sequence[str], None] = 'a7c2e5f91b36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Corrige o fluxo de criação de chaveamento (UC014) para os formatos
    KNOCKOUT e GROUP_STAGE_KNOCKOUT: o sorteio insere todas as partidas de
    uma árvore de mata-mata num único batch, já com `next_match_id`
    auto-referenciado apontando para a partida da fase seguinte (ex.:
    SEMIFINAL -> FINAL). Como as partidas de rodadas anteriores aparecem
    na lista (e portanto no INSERT) antes da partida que elas referenciam,
    a FK `fk_matches_next_match_id` - por padrão checada linha a linha,
    na ordem do INSERT - rejeitava o insert com ForeignKeyViolationError,
    mesmo com o id de destino presente no mesmo batch/transação.

    Tornar a constraint DEFERRABLE INITIALLY DEFERRED faz o Postgres
    validá-la apenas no COMMIT da transação, quando todas as partidas já
    foram inseridas - resolvendo o problema independentemente da ordem de
    inserção gerada pelo draw_engine.
    """
    op.drop_constraint('fk_matches_next_match_id', 'matches', type_='foreignkey')
    op.create_foreign_key(
        'fk_matches_next_match_id',
        'matches',
        'matches',
        ['next_match_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_matches_next_match_id', 'matches', type_='foreignkey')
    op.create_foreign_key(
        'fk_matches_next_match_id', 'matches', 'matches', ['next_match_id'], ['id']
    )
