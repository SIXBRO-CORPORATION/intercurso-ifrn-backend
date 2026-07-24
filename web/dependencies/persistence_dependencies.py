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
from persistence.adapters.bracket_repository_adapter import BracketRepositoryAdapter
from persistence.adapters.bracket_group_repository_adapter import (
    BracketGroupRepositoryAdapter,
)
from persistence.adapters.bracket_group_team_repository_adapter import (
    BracketGroupTeamRepositoryAdapter,
)
from persistence.adapters.match_repository_adapter import MatchRepositoryAdapter
from persistence.adapters.match_event_repository_adapter import (
    MatchEventRepositoryAdapter,
)
from persistence.adapters.modality_configuration_repository_adapter import (
    ModalityConfigurationRepositoryAdapter,
)
from persistence.adapters.volleyball_modality_configuration_repository_adapter import (
    VolleyballModalityConfigurationRepositoryAdapter,
)
from persistence.adapters.match_set_repository_adapter import (
    MatchSetRepositoryAdapter,
)
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.refresh_token_repository_port import RefreshTokenRepositoryPort
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.bracket_group_repository_port import BracketGroupRepositoryPort
from core.persistence.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from core.persistence.match_set_repository_port import MatchSetRepositoryPort
from persistence.database import get_db
from persistence.mappers.team_mapper import TeamMapper
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper
from persistence.mappers.season_mapper import SeasonMapper
from persistence.mappers.season_modality_mapper import SeasonModalityMapper
from persistence.mappers.modality_mapper import ModalityMapper
from persistence.mappers.refresh_token_mapper import RefreshTokenMapper
from persistence.mappers.bracket_mapper import BracketMapper
from persistence.mappers.bracket_group_mapper import BracketGroupMapper
from persistence.mappers.bracket_group_team_mapper import BracketGroupTeamMapper
from persistence.mappers.match_mapper import MatchMapper
from persistence.mappers.match_event_mapper import MatchEventMapper
from persistence.mappers.modality_configuration_mapper import (
    ModalityConfigurationMapper,
)
from persistence.mappers.volleyball_modality_configuration_mapper import (
    VolleyballModalityConfigurationMapper,
)
from persistence.mappers.match_set_mapper import MatchSetMapper


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


def get_bracket_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BracketRepositoryPort:
    mapper = BracketMapper()

    return BracketRepositoryAdapter(session, mapper)


def get_bracket_group_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BracketGroupRepositoryPort:
    mapper = BracketGroupMapper()

    return BracketGroupRepositoryAdapter(session, mapper)


def get_bracket_group_team_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BracketGroupTeamRepositoryPort:
    mapper = BracketGroupTeamMapper()

    return BracketGroupTeamRepositoryAdapter(session, mapper)


def get_match_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRepositoryPort:
    mapper = MatchMapper()

    return MatchRepositoryAdapter(session, mapper)


def get_match_event_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MatchEventRepositoryPort:
    mapper = MatchEventMapper()

    return MatchEventRepositoryAdapter(session, mapper)


def get_modality_configuration_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ModalityConfigurationRepositoryPort:
    mapper = ModalityConfigurationMapper()

    return ModalityConfigurationRepositoryAdapter(session, mapper)


def get_volleyball_modality_configuration_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VolleyballModalityConfigurationRepositoryPort:
    mapper = VolleyballModalityConfigurationMapper()

    return VolleyballModalityConfigurationRepositoryAdapter(session, mapper)


def get_match_set_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MatchSetRepositoryPort:
    mapper = MatchSetMapper()

    return MatchSetRepositoryAdapter(session, mapper)
