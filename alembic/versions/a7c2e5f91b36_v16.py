"""v16

Revision ID: a7c2e5f91b36
Revises: c5e9a1d72b43
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c2e5f91b36'
down_revision: Union[str, Sequence[str], None] = 'c5e9a1d72b43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Frequência (%) do aluno no SUAP, atualizada a cada login (UC009)."""
    op.add_column('users', sa.Column('frequencia_percentual', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'frequencia_percentual')
