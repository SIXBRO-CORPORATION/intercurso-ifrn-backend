from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from persistence.adapters.user_repository_adapter import UserRepositoryAdapter
from persistence.adapters.team_repository_adapter import TeamRepositoryAdapter
from persistence.adapters.team_member_repository_adapter import (
    TeamMemberRepositoryAdapter,
)
from persistence.adapters.season_repository_adapter import SeasonRepositoryAdapter
from persistence.adapters.season_modality_repository_adapter import (
    SeasonModalityRepositoryAdapter,
)
from persistence.adapters.modality_repository_adapter import ModalityRepositoryAdapter
from persistence.adapters.refresh_token_adapter import RefreshTokenRepositoryAdapter
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.refresh_token_repository_port import RefreshTokenRepositoryPort
from persistence.database import get_db
from persistence.mappers.team_mapper import TeamMapper
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper
from persistence.mappers.season_mapper import SeasonMapper
from persistence.mappers.season_modality_mapper import SeasonModalityMapper
from persistence.mappers.modality_mapper import ModalityMapper
from persistence.mappers.refresh_token_mapper import RefreshTokenMapper


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepositoryPort:
    mapper = UserMapper()

    return UserRepositoryAdapter(session, mapper)


def get_team_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TeamRepositoryPort:
    mapper = TeamMapper()

    return TeamRepositoryAdapter(session, mapper)


def get_team_member_repository(
    session: Annotated[Session, Depends(get_db)],
) -> TeamMemberRepositoryPort:
    team_member_mapper = TeamMemberMapper()
    user_mapper = UserMapper()

    return TeamMemberRepositoryAdapter(session, team_member_mapper, user_mapper)


def get_season_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SeasonRepositoryPort:
    mapper = SeasonMapper()

    return SeasonRepositoryAdapter(session, mapper)


def get_season_modality_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SeasonModalityRepositoryPort:
    mapper = SeasonModalityMapper()

    return SeasonModalityRepositoryAdapter(session, mapper)


def get_modality_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ModalityRepositoryPort:
    mapper = ModalityMapper()

    return ModalityRepositoryAdapter(session, mapper)


def get_refresh_token_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshTokenRepositoryPort:
    mapper = RefreshTokenMapper()

    return RefreshTokenRepositoryAdapter(session, mapper)
