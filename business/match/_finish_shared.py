from datetime import datetime
from typing import Optional
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.event_type import EventType
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.match.match_event import MatchEvent


def determine_winner_id(
    match: Match, penalty_result: Optional[dict]
) -> Optional[UUID]:
    if penalty_result:
        winner_id = penalty_result.get("winner_id")
        return UUID(winner_id) if isinstance(winner_id, str) else winner_id
    team1_score = match.team1_score or 0
    team2_score = match.team2_score or 0
    if team1_score > team2_score:
        return match.team1_id
    if team2_score > team1_score:
        return match.team2_id
    return None


def ensure_knockout_tie_requires_penalties(
    match: Match, penalty_result: Optional[dict]
) -> None:

    if match.match_category != MatchCategory.KNOCKOUT:
        return
    if penalty_result is not None:
        return
    if (match.team1_score or 0) == (match.team2_score or 0):
        raise BusinessException(
            "Partida empatada em mata-mata no tempo regulamentar. Inicie a "
            "disputa de pênaltis (POST /api/match/{match_id}/penalty-shootout/start) "
            "antes de finalizar a partida."
        )


def ensure_penalty_shootout_can_start(match: Match) -> None:
    if match.match_category != MatchCategory.KNOCKOUT:
        raise BusinessException(
            "Disputa de pênaltis só é aplicável a partidas de mata-mata (KNOCKOUT)"
        )
    if (match.team1_score or 0) != (match.team2_score or 0):
        raise BusinessException(
            "Só é possível iniciar disputa de pênaltis em partidas empatadas "
            "no tempo regulamentar"
        )
    if match.penalty_shootout_active:
        raise BusinessException(
            "Disputa de pênaltis já está em andamento para esta partida"
        )
    if match.penality_result:
        raise BusinessException(
            "Esta partida já teve sua disputa de pênaltis encerrada"
        )


def ensure_penalty_shootout_active(match: Match) -> None:
    if not match.penalty_shootout_active:
        raise BusinessException(
            "Disputa de pênaltis não foi iniciada para esta partida "
            "(POST /api/match/{match_id}/penalty-shootout/start)"
        )


async def advance_knockout_winner(
    match_repository: MatchRepositoryPort,
    match: Match,
    winner_id: Optional[UUID],
) -> None:

    if winner_id is None or match.next_match_id is None:
        return

    next_match = await match_repository.lock_for_update(match.next_match_id)
    if next_match is None:
        return

    if next_match.team1_id is None:
        next_match.team1_id = winner_id
    elif next_match.team2_id is None:
        next_match.team2_id = winner_id
    else:

        return

    await match_repository.save(next_match)


async def advance_semifinal_loser(
    match_repository: MatchRepositoryPort,
    match: Match,
    winner_id: Optional[UUID],
) -> None:

    if match.match_type != MatchType.SEMIFINAL or winner_id is None:
        return

    loser_id = match.team2_id if winner_id == match.team1_id else match.team1_id
    if loser_id is None:
        return

    third_place_match = await match_repository.find_by_bracket_and_type(
        match.bracket_id, MatchType.THIRD_PLACE
    )
    if third_place_match is None:
        return

    locked_third_place_match = await match_repository.lock_for_update(
        third_place_match.id
    )
    if locked_third_place_match is None:
        return

    if locked_third_place_match.team1_id is None:
        locked_third_place_match.team1_id = loser_id
    elif locked_third_place_match.team2_id is None:
        locked_third_place_match.team2_id = loser_id
    else:
        return

    await match_repository.save(locked_third_place_match)


async def update_group_standings(
    bracket_group_team_repository: BracketGroupTeamRepositoryPort,
    match: Match,
    winner_id: Optional[UUID],
) -> None:
    """RN16-18 (Fluxo Principal passo 12 / Alternativo 2): atualiza a
    classificação (BracketGroupTeam) dos dois times da partida de grupo."""
    if match.bracket_group_id is None:
        return

    team1_standing = await bracket_group_team_repository.find_by_bracket_group_and_team(
        match.bracket_group_id, match.team1_id
    )
    team2_standing = await bracket_group_team_repository.find_by_bracket_group_and_team(
        match.bracket_group_id, match.team2_id
    )
    if team1_standing is None or team2_standing is None:
        return

    team1_goals = match.team1_score or 0
    team2_goals = match.team2_score or 0

    team1_standing.goals_for = (team1_standing.goals_for or 0) + team1_goals
    team1_standing.goals_against = (team1_standing.goals_against or 0) + team2_goals
    team2_standing.goals_for = (team2_standing.goals_for or 0) + team2_goals
    team2_standing.goals_against = (team2_standing.goals_against or 0) + team1_goals

    if winner_id is None:
        team1_standing.points = (team1_standing.points or 0) + 1
        team2_standing.points = (team2_standing.points or 0) + 1
        team1_standing.draws = (team1_standing.draws or 0) + 1
        team2_standing.draws = (team2_standing.draws or 0) + 1
    elif winner_id == match.team1_id:
        team1_standing.points = (team1_standing.points or 0) + 3
        team1_standing.wins = (team1_standing.wins or 0) + 1
        team2_standing.losses = (team2_standing.losses or 0) + 1
    else:
        team2_standing.points = (team2_standing.points or 0) + 3
        team2_standing.wins = (team2_standing.wins or 0) + 1
        team1_standing.losses = (team1_standing.losses or 0) + 1

    team1_standing.goals_difference = (
        team1_standing.goals_for - team1_standing.goals_against
    )
    team2_standing.goals_difference = (
        team2_standing.goals_for - team2_standing.goals_against
    )

    await bracket_group_team_repository.save(team1_standing)
    await bracket_group_team_repository.save(team2_standing)


async def finalize_match(
    match: Match,
    monitor_id: UUID,
    match_repository: MatchRepositoryPort,
    match_event_repository: MatchEventRepositoryPort,
    bracket_group_team_repository: BracketGroupTeamRepositoryPort,
    audit_logger: AuditLogger,
    penalty_result: Optional[dict] = None,
) -> Match:
    winner_id = determine_winner_id(match, penalty_result)

    if match.match_category == MatchCategory.KNOCKOUT and winner_id is None:

        raise BusinessException(
            "Não é possível finalizar uma partida de mata-mata sem um vencedor definido"
        )

    now = datetime.now()
    match.sync_clock(now)
    match.status = MatchStatus.FINISHED
    match.finished_at = now
    match.clock_running = False
    match.winner_id = winner_id
    if penalty_result is not None:
        match.penality_result = penalty_result

    saved_match = await match_repository.save(match)

    match_end_event = MatchEvent(
        match_id=saved_match.id,
        event_type=EventType.MATCH_END,
        clock_seconds=saved_match.clock_seconds or 0,
        metadata_json={"winner_id": str(winner_id)} if winner_id else {},
    )
    await match_event_repository.save(match_end_event)

    if saved_match.match_category == MatchCategory.KNOCKOUT:
        await advance_knockout_winner(match_repository, saved_match, winner_id)
        await advance_semifinal_loser(match_repository, saved_match, winner_id)
    else:
        await update_group_standings(
            bracket_group_team_repository, saved_match, winner_id
        )

    result_description = f"{saved_match.team1_score}x{saved_match.team2_score}"
    if penalty_result:
        result_description += (
            f" (pênaltis {penalty_result.get('team1_penalties')}x"
            f"{penalty_result.get('team2_penalties')})"
        )
    winner_description = str(winner_id) if winner_id else "empate"
    await audit_logger.log(
        action=AuditAction.MATCH_FINISHED,
        description=(
            f"Partida {saved_match.id} finalizada ({result_description}). "
            f"Vencedor: {winner_description}"
        ),
        actor_id=monitor_id,
    )

    return saved_match
