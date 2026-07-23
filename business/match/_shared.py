from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.event_type import EventType
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match import Match
from domain.modality import Modality
from domain.modality_configuration import ModalityConfiguration
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User


async def validate_match_in_progress(
    match_repository,
    match_id: Optional[UUID],
    monitor_id: Optional[UUID],
) -> Match:
    if match_id is None:
        raise BusinessException("Partida é obrigatória")
    if monitor_id is None:
        raise BusinessException("Monitor responsável é obrigatório")

    match = await match_repository.get(match_id)
    if match is None:
        raise BusinessException("Partida não encontrada")

    if match.status != MatchStatus.IN_PROGRESS:
        status_atual = match.status.value if match.status else "desconhecido"
        raise BusinessException(
            "Só é possível registrar eventos em partidas em andamento "
            f"(IN_PROGRESS). Status atual: {status_atual}"
        )

    if match.monitor_id != monitor_id:
        raise BusinessException(
            "Apenas o monitor responsável por esta partida pode registrar eventos"
        )

    return match


def pause_clock(match: Match, now: Optional[datetime] = None) -> None:
    match.sync_clock(now)
    match.clock_running = False


async def validate_team_in_match(match: Match, team_id: Optional[UUID]) -> None:
    if team_id is None:
        raise BusinessException("Time é obrigatório")
    if team_id not in (match.team1_id, match.team2_id):
        raise BusinessException("Time informado não participa desta partida")


async def validate_player_in_team(
    team_member_repository: TeamMemberRepositoryPort,
    team_id: UUID,
    player_id: Optional[UUID],
) -> TeamMember:
    if player_id is None:
        raise BusinessException("Jogador é obrigatório")

    members = await team_member_repository.find_members_by_team_id(team_id)
    member = next((m for m in members if m.user_id == player_id), None)
    if member is None:
        raise BusinessException("Jogador informado não pertence ao time")
    return member


async def is_player_expelled(
    match_event_repository: MatchEventRepositoryPort,
    match_id: UUID,
    player_id: UUID,
) -> bool:
    expulsions = await match_event_repository.find_by_match_and_type(
        match_id, EventType.EXPULSION
    )
    return any(event.player_id == player_id for event in expulsions)


async def load_modality_configuration(
    bracket_repository: BracketRepositoryPort,
    modality_repository: ModalityRepositoryPort,
    modality_configuration_repository: ModalityConfigurationRepositoryPort,
    bracket_id: UUID,
) -> Tuple[Optional[Modality], Optional[ModalityConfiguration]]:
    bracket = await bracket_repository.get(bracket_id)
    if bracket is None:
        return None, None

    modality = await modality_repository.get(bracket.modality_id)
    modality_configuration = await modality_configuration_repository.find_by_modality(
        bracket.modality_id
    )
    return modality, modality_configuration


async def load_players(
    team_member_repository: TeamMemberRepositoryPort,
    user_repository: UserRepositoryPort,
    team_id: UUID,
) -> List[Tuple[TeamMember, User]]:
    members = await team_member_repository.find_members_by_team_id(team_id)
    players: List[Tuple[TeamMember, User]] = []
    for member in members:
        user = await user_repository.get(member.user_id)
        if user is not None:
            players.append((member, user))
    return players


async def load_management_context(
    context,
    match: Match,
    team_repository: TeamRepositoryPort,
    team_member_repository: TeamMemberRepositoryPort,
    user_repository: UserRepositoryPort,
    bracket_repository: BracketRepositoryPort,
    modality_repository: ModalityRepositoryPort,
    modality_configuration_repository: ModalityConfigurationRepositoryPort,
    match_event_repository: MatchEventRepositoryPort,
) -> None:

    team1 = await team_repository.get(match.team1_id)
    team2 = await team_repository.get(match.team2_id)

    team1_players = await load_players(team_member_repository, user_repository, match.team1_id)
    team2_players = await load_players(team_member_repository, user_repository, match.team2_id)

    modality, modality_configuration = await load_modality_configuration(
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        match.bracket_id,
    )

    timeline_events = await match_event_repository.find_by_match(match.id)

    context.put_property("team1", team1)
    context.put_property("team2", team2)
    context.put_property("team1_players", team1_players)
    context.put_property("team2_players", team2_players)
    if modality is not None:
        context.put_property("modality", modality)
    if modality_configuration is not None:
        context.put_property("modality_configuration", modality_configuration)
    context.put_property("timeline_events", timeline_events)
