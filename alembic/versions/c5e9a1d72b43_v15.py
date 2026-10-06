"""v15

Revision ID: c5e9a1d72b43
Revises: f3a4b7c91d22
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e9a1d72b43'
down_revision: Union[str, Sequence[str], None] = 'f3a4b7c91d22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Motivo de rejeição de time (UC009, sugestão futura implementada)."""
    op.add_column('teams', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('teams', 'rejection_reason')
