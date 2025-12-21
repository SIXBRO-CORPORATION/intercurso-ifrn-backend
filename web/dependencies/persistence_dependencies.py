from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from persistence.adapters.user_repository_adapter import UserRepositoryAdapter
from persistence.adapters.team_repository_adapter import TeamRepositoryAdapter
from persistence.adapters.team_member_repository_adapter import (
    TeamMemberRepositoryAdapter,
)
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from persistence.database import get_db
from persistence.mappers.team_mapper import TeamMapper
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper


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
