"""v14

Revision ID: f3a4b7c91d22
Revises: b7e3d91c4a20
Create Date: 2026-10-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a4b7c91d22'
down_revision: Union[str, Sequence[str], None] = 'b7e3d91c4a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Regulamento Jogos Internos 2026 (Art. 10, §1º-§3º): modalidades são
    diferenciadas por gênero (masculino/feminino como modalidades distintas,
    cada uma com seu próprio chaveamento) ou mistas com cota mínima de cada
    gênero por equipe (Voleibol, Queimada, Handebol). Para validar isso é
    necessário saber o gênero do atleta — dado que não existia no sistema e
    passa a ser capturado via SUAP (/api/rh/eu). Aproveitamos para também
    persistir outros dados de identificação do SUAP que hoje são obtidos mas
    descartados (curso, campus, tipo_usuario etc.), para uso futuro
    (elegibilidade, analytics).
    """
    op.add_column('users', sa.Column('gender', sa.String(length=1), nullable=True))
    op.add_column('users', sa.Column('tipo_usuario', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('campus', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('curso', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('turno', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('email_classroom', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('photo', sa.String(), nullable=True))
    op.add_column('users', sa.Column('birth_date', sa.Date(), nullable=True))

    op.add_column(
        'modalities',
        sa.Column('gender_mode', sa.String(length=10), nullable=False, server_default='MIXED'),
    )
    op.add_column('modalities', sa.Column('min_male_members', sa.Integer(), nullable=True))
    op.add_column('modalities', sa.Column('min_female_members', sa.Integer(), nullable=True))

    # server_default só existe para preencher as linhas já existentes sem
    # quebrar o NOT NULL; daqui pra frente o cadastro (UC004) sempre exige
    # que o monitor escolha gender_mode explicitamente.
    op.alter_column('modalities', 'gender_mode', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('modalities', 'min_female_members')
    op.drop_column('modalities', 'min_male_members')
    op.drop_column('modalities', 'gender_mode')

    op.drop_column('users', 'birth_date')
    op.drop_column('users', 'photo')
    op.drop_column('users', 'email_classroom')
    op.drop_column('users', 'turno')
    op.drop_column('users', 'curso')
    op.drop_column('users', 'campus')
    op.drop_column('users', 'tipo_usuario')
    op.drop_column('users', 'gender')
