from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from business.match._shared import load_modality_configuration
from core.business.audit.audit_logger import AuditLogger
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.match.match_set_repository_port import MatchSetRepositoryPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.event_type import EventType
from domain.enums.match_status import MatchStatus
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.match.match_event import MatchEvent

NON_CORRECTABLE_EVENT_TYPES = frozenset(
    {
        EventType.MATCH_STARTED,
        EventType.MATCH_END,
        EventType.PERIOD_START,
        EventType.PERIOD_END,
    }
)


@dataclass
class CorrectionResult:
    match: Match
    corrected_event: MatchEvent
    reactivated_player_id: Optional[UUID] = None
    correction_alert: Optional[dict] = None


def ensure_event_correctable(event_type: Optional[EventType]) -> None:
    if event_type in NON_CORRECTABLE_EVENT_TYPES:
        raise BusinessException(
            "Este tipo de evento não pode ser desfeito/deletado "
            f"({event_type.value if event_type else 'desconhecido'})"
        )


async def validate_match_correctable(
    match_repository: MatchRepositoryPort,
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

    if match.status not in (MatchStatus.IN_PROGRESS, MatchStatus.FINISHED):
        status_atual = match.status.value if match.status else "desconhecido"
        raise BusinessException(
            "Só é possível corrigir eventos em partidas em andamento "
            f"(IN_PROGRESS) ou finalizadas (FINISHED). Status atual: {status_atual}"
        )

    if match.status == MatchStatus.IN_PROGRESS and match.monitor_id != monitor_id:
        raise BusinessException(
            "Apenas o monitor responsável por esta partida pode corrigir "
            "eventos enquanto ela está em andamento"
        )

    return match


async def find_last_correctable_event(
    match_event_repository: MatchEventRepositoryPort,
    match_id: UUID,
) -> MatchEvent:

    events = await match_event_repository.find_by_match(match_id)
    correctable = [
        event for event in events if event.event_type not in NON_CORRECTABLE_EVENT_TYPES
    ]
    if not correctable:
        raise BusinessException(
            "Não há eventos que possam ser desfeitos nesta partida"
        )
    return max(correctable, key=lambda event: event.created_at or datetime.min)


async def get_correctable_event(
    match_event_repository: MatchEventRepositoryPort,
    match_id: UUID,
    event_id: Optional[UUID],
) -> MatchEvent:
    if event_id is None:
        raise BusinessException("Evento é obrigatório")

    event = await match_event_repository.get(event_id)
    if event is None or event.match_id != match_id:
        raise BusinessException("Evento não encontrado nesta partida")
    return event


async def _find_linked_expulsion(
    match_event_repository: MatchEventRepositoryPort,
    card_event: MatchEvent,
) -> Optional[MatchEvent]:

    if card_event.player_id is None:
        return None

    expulsions = await match_event_repository.find_by_match_and_type(
        card_event.match_id, EventType.EXPULSION
    )
    same_clock = [
        e
        for e in expulsions
        if e.player_id == card_event.player_id
        and e.clock_seconds == card_event.clock_seconds
    ]
    if same_clock:
        return same_clock[0]

    by_player = [e for e in expulsions if e.player_id == card_event.player_id]
    return by_player[0] if by_player else None


async def _reverse_expulsion_if_needed(
    match_event_repository: MatchEventRepositoryPort,
    target_event: MatchEvent,
) -> Optional[UUID]:

    if target_event.event_type == EventType.EXPULSION:
        return target_event.player_id

    triggers_expulsion_removal = target_event.event_type == EventType.CARD_RED or (
        target_event.event_type == EventType.CARD_YELLOW
        and (target_event.metadata_json or {}).get("previous_cards", 0) >= 1
    )
    if not triggers_expulsion_removal:
        return None

    linked_expulsion = await _find_linked_expulsion(match_event_repository, target_event)
    if linked_expulsion is None:
        return None

    await match_event_repository.soft_delete_event(linked_expulsion.id)
    return target_event.player_id


async def _recompute_running_score(
    match: Match,
    match_event_repository: MatchEventRepositoryPort,
    is_sets_modality: bool,
) -> None:

    events = await match_event_repository.find_by_match(match.id)

    boundary_created_at = None
    if is_sets_modality:
        set_end_events = [e for e in events if e.event_type == EventType.SET_END]
        if set_end_events:
            last_set_end = max(
                set_end_events, key=lambda e: e.created_at or datetime.min
            )
            boundary_created_at = last_set_end.created_at

    team1_score = 0
    team2_score = 0
    for event in events:
        if event.event_type not in (EventType.GOAL, EventType.POINT):
            continue
        if boundary_created_at is not None and (
            (event.created_at or datetime.min) <= boundary_created_at
        ):
            continue
        if event.team_id == match.team1_id:
            team1_score += 1
        elif event.team_id == match.team2_id:
            team2_score += 1

    match.team1_score = team1_score
    match.team2_score = team2_score


async def _recompute_sets_won(
    match: Match, match_set_repository: MatchSetRepositoryPort
) -> None:
    sets_won = await match_set_repository.count_sets_won_by_team(match.id)
    match.team1_sets_won = sets_won.get(match.team1_id, 0)
    match.team2_sets_won = sets_won.get(match.team2_id, 0)


async def _revert_set_end(
    match: Match,
    set_end_event: MatchEvent,
    match_set_repository: MatchSetRepositoryPort,
) -> None:

    set_number = (set_end_event.metadata_json or {}).get("set_number")
    if set_number is None:
        return

    match_sets = await match_set_repository.find_by_match(match.id)
    target_set = next(
        (s for s in match_sets if s.set_number == set_number), None
    )
    if target_set is None:
        return

    await match_set_repository.soft_delete_set(target_set.id)


async def _recompute_penalty_score(
    match: Match, match_event_repository: MatchEventRepositoryPort
) -> None:

    events = await match_event_repository.find_by_match(match.id)

    team1_penalties = sum(
        1
        for e in events
        if e.event_type == EventType.PENALTY_GOAL and e.team_id == match.team1_id
    )
    team2_penalties = sum(
        1
        for e in events
        if e.event_type == EventType.PENALTY_GOAL and e.team_id == match.team2_id
    )

    match.team1_penalty_score = team1_penalties
    match.team2_penalty_score = team2_penalties

    if match.penality_result:
        updated_result = dict(match.penality_result)
        updated_result["team1_penalties"] = team1_penalties
        updated_result["team2_penalties"] = team2_penalties
        if team1_penalties != team2_penalties:
            winner_id = (
                match.team1_id if team1_penalties > team2_penalties else match.team2_id
            )
            updated_result["winner_id"] = str(winner_id)
        match.penality_result = updated_result


def _score_snapshot(match: Match) -> tuple:
    return (
        match.team1_score,
        match.team2_score,
        match.team1_sets_won,
        match.team2_sets_won,
        match.team1_penalty_score,
        match.team2_penalty_score,
    )


def _build_post_finish_alert(
    match: Match,
    previous_snapshot: tuple,
    previous_winner_id: Optional[UUID],
) -> dict:

    (
        prev_team1_score,
        prev_team2_score,
        prev_team1_sets,
        prev_team2_sets,
        _prev_team1_penalty,
        _prev_team2_penalty,
    ) = previous_snapshot

    if match.team1_sets_won is not None or match.team2_sets_won is not None:
        previous_score = f"{prev_team1_sets or 0}x{prev_team2_sets or 0} (sets)"
        corrected_score = f"{match.team1_sets_won or 0}x{match.team2_sets_won or 0} (sets)"
        current_winner_id = (
            match.team1_id
            if (match.team1_sets_won or 0) > (match.team2_sets_won or 0)
            else match.team2_id
            if (match.team2_sets_won or 0) > (match.team1_sets_won or 0)
            else None
        )
    else:
        previous_score = f"{prev_team1_score or 0}x{prev_team2_score or 0}"
        corrected_score = f"{match.team1_score or 0}x{match.team2_score or 0}"
        current_winner_id = (
            match.team1_id
            if (match.team1_score or 0) > (match.team2_score or 0)
            else match.team2_id
            if (match.team2_score or 0) > (match.team1_score or 0)
            else None
        )

    winner_changed = current_winner_id != previous_winner_id
    if current_winner_id is None:
        current_status = "EMPATE"
    elif winner_changed:
        current_status = "NOVO VENCEDOR"
    else:
        current_status = "VENCEDOR MANTIDO"

    return {
        "alert_type": "CRITICAL",
        "previous_score": previous_score,
        "corrected_score": corrected_score,
        "previous_winner_id": str(previous_winner_id) if previous_winner_id else None,
        "current_winner_id": str(current_winner_id) if current_winner_id else None,
        "current_status": current_status,
        "required_actions": [
            "Verificar se o time correto avançou no chaveamento (UC012)",
            "Corrigir manualmente a próxima fase se necessário",
            "Notificar os alunos sobre a correção",
            "Registrar a justificativa da alteração",
        ],
        "note": (
            "O vencedor da partida (winner_id) NÃO foi alterado "
            "automaticamente. Esta correção foi registrada em auditoria "
            "com destaque especial."
        ),
    }


def _describe_event(event: MatchEvent) -> str:
    label = event.event_type.value if event.event_type else "evento"
    return f"{label} (id={event.id})"


async def apply_event_correction(
    match: Match,
    target_event: MatchEvent,
    monitor_id: UUID,
    *,
    match_repository: MatchRepositoryPort,
    match_event_repository: MatchEventRepositoryPort,
    match_set_repository: MatchSetRepositoryPort,
    bracket_repository: BracketRepositoryPort,
    modality_repository: ModalityRepositoryPort,
    modality_configuration_repository: ModalityConfigurationRepositoryPort,
    audit_logger: AuditLogger,
    normal_audit_action: AuditAction,
) -> CorrectionResult:

    ensure_event_correctable(target_event.event_type)

    was_finished = match.status == MatchStatus.FINISHED
    previous_snapshot = _score_snapshot(match)
    previous_winner_id = match.winner_id

    deleted = await match_event_repository.soft_delete_event(target_event.id)
    if not deleted:
        raise BusinessException(
            "Evento não encontrado ou já havia sido corrigido anteriormente"
        )

    reactivated_player_id = await _reverse_expulsion_if_needed(
        match_event_repository, target_event
    )

    _, modality_configuration = await load_modality_configuration(
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        match.bracket_id,
    )
    is_sets_modality = (
        modality_configuration is not None
        and modality_configuration.score_type == ScoreType.SETS
    )

    if target_event.event_type == EventType.SET_END and is_sets_modality:
        await _revert_set_end(match, target_event, match_set_repository)

    if is_sets_modality:
        await _recompute_sets_won(match, match_set_repository)

    if target_event.event_type in (EventType.GOAL, EventType.POINT, EventType.SET_END):
        await _recompute_running_score(match, match_event_repository, is_sets_modality)

    if target_event.event_type in (EventType.PENALTY_GOAL, EventType.PENALTY_MISS):
        await _recompute_penalty_score(match, match_event_repository)

    match.sync_clock()
    saved_match = await match_repository.save(match)

    correction_alert = None
    if was_finished and _score_snapshot(saved_match) != previous_snapshot:
        correction_alert = _build_post_finish_alert(
            saved_match, previous_snapshot, previous_winner_id
        )

    audit_action = (
        AuditAction.MATCH_POST_FINISH_CORRECTION if was_finished else normal_audit_action
    )
    description = (
        f"Partida {saved_match.id}: correção de {_describe_event(target_event)}."
    )
    if was_finished:
        description += " Correção realizada após a partida já estar FINALIZADA."
    if correction_alert is not None:
        description += (
            f" Placar mudou de {correction_alert['previous_score']} para "
            f"{correction_alert['corrected_score']}."
        )
    await audit_logger.log(
        action=audit_action,
        description=description,
        actor_id=monitor_id,
    )

    return CorrectionResult(
        match=saved_match,
        corrected_event=target_event,
        reactivated_player_id=reactivated_player_id,
        correction_alert=correction_alert,
    )
