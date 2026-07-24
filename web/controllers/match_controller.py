from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.match.start_match_port import StartMatchPort
from core.business.match.register_goal_port import RegisterGoalPort
from core.business.match.register_card_port import RegisterCardPort
from core.business.match.pause_clock_port import PauseClockPort
from core.business.match.resume_clock_port import ResumeClockPort
from core.business.match.end_period_port import EndPeriodPort
from core.business.match.start_period_port import StartPeriodPort
from core.business.match.end_set_port import EndSetPort
from core.context import Context
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.match.match_event import MatchEvent
from domain.team.team import Team
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_end_period_port,
    get_end_set_port,
    get_match_model_mapper,
    get_pause_clock_port,
    get_register_card_port,
    get_register_goal_port,
    get_resume_clock_port,
    get_start_match_port,
    get_start_period_port,
    require_monitor,
)
from web.mappers.match_model_mapper import MatchModelMapper
from web.models.request.match.match_card_request import MatchCardRequest
from web.models.request.match.match_goal_request import MatchGoalRequest
from web.models.response.match.match_management_response import MatchManagementResponse

router = APIRouter(prefix="/api/match", tags=["match"])

# TODO (débito técnico Fase 5): endpoints de consulta (GET de partida por id,
# GET de partidas por temporada/time) e os demais casos de uso da fase
# (UC015 - Finalizar Partida, UC017 - Corrigir Evento) ficam para as próximas
# rodadas desta fase, conforme o planejamento em docs/ai/planejamento.md.
# UC016 (WebSocket) e Push Notifications também são débito técnico (Fase 6):
# nenhum evento abaixo dispara notificação em tempo real ainda.


def _build_response(
    context: Context,
    mapper: MatchModelMapper,
    match,
    default_message: str,
) -> ApiResponse[MatchManagementResponse]:
    team1 = context.get_property("team1", Team)
    team2 = context.get_property("team2", Team)
    team1_players = context.get_property("team1_players", list) or []
    team2_players = context.get_property("team2_players", list) or []
    modality = context.get_property("modality", Modality)
    modality_configuration = context.get_property(
        "modality_configuration", ModalityConfiguration
    )
    timeline_events: List[MatchEvent] = (
        context.get_property("timeline_events", list) or []
    )
    match_point_reached = context.get("match_point_reached")

    response_data = mapper.to_management_response(
        match,
        team1,
        team2,
        team1_players,
        team2_players,
        modality,
        modality_configuration,
        timeline_events,
        match_point_reached,
    )

    return ApiResponse(data=response_data, message=default_message)


@router.post(
    "/{match_id}/start",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def start_match(
    match_id: UUID,
    start_match_port: Annotated[StartMatchPort, Depends(get_start_match_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    started_match = await start_match_port.execute(context)

    team1 = context.get_property("team1", Team)
    team2 = context.get_property("team2", Team)
    team1_players = context.get_property("team1_players", list) or []
    team2_players = context.get_property("team2_players", list) or []
    modality = context.get_property("modality", Modality)
    modality_configuration = context.get_property(
        "modality_configuration", ModalityConfiguration
    )
    match_start_event = context.get_property("match_start_event", MatchEvent)
    timeline_events = [match_start_event] if match_start_event else []

    response_data = mapper.to_management_response(
        started_match,
        team1,
        team2,
        team1_players,
        team2_players,
        modality,
        modality_configuration,
        timeline_events,
    )

    return ApiResponse(
        data=response_data, message="Partida iniciada com sucesso!"
    )


@router.post(
    "/{match_id}/goal",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def register_goal(
    match_id: UUID,
    request: MatchGoalRequest,
    register_goal_port: Annotated[RegisterGoalPort, Depends(get_register_goal_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)
    context.put_property("team_id", request.team_id)
    context.put_property("player_id", request.player_id)

    match = await register_goal_port.execute(context)

    return _build_response(context, mapper, match, "Gol/ponto registrado com sucesso!")


@router.post(
    "/{match_id}/card",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def register_card(
    match_id: UUID,
    request: MatchCardRequest,
    register_card_port: Annotated[RegisterCardPort, Depends(get_register_card_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)
    context.put_property("team_id", request.team_id)
    context.put_property("player_id", request.player_id)
    context.put_property("card_type", request.card_type)

    match = await register_card_port.execute(context)

    return _build_response(context, mapper, match, "Cartão registrado com sucesso!")


@router.post(
    "/{match_id}/clock/pause",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def pause_clock(
    match_id: UUID,
    pause_clock_port: Annotated[PauseClockPort, Depends(get_pause_clock_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    match = await pause_clock_port.execute(context)

    return _build_response(context, mapper, match, "Cronômetro pausado com sucesso!")


@router.post(
    "/{match_id}/clock/resume",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def resume_clock(
    match_id: UUID,
    resume_clock_port: Annotated[ResumeClockPort, Depends(get_resume_clock_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    match = await resume_clock_port.execute(context)

    return _build_response(context, mapper, match, "Cronômetro retomado com sucesso!")


@router.post(
    "/{match_id}/period/end",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def end_period(
    match_id: UUID,
    end_period_port: Annotated[EndPeriodPort, Depends(get_end_period_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    match = await end_period_port.execute(context)

    return _build_response(context, mapper, match, "Período encerrado com sucesso!")


@router.post(
    "/{match_id}/period/start",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def start_period(
    match_id: UUID,
    start_period_port: Annotated[StartPeriodPort, Depends(get_start_period_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    match = await start_period_port.execute(context)

    return _build_response(context, mapper, match, "Próximo período iniciado com sucesso!")


@router.post(
    "/{match_id}/set/end",
    response_model=ApiResponse[MatchManagementResponse],
    status_code=status.HTTP_200_OK,
)
async def end_set(
    match_id: UUID,
    end_set_port: Annotated[EndSetPort, Depends(get_end_set_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", current_user.id)

    match = await end_set_port.execute(context)

    return _build_response(context, mapper, match, "Set finalizado com sucesso!")
