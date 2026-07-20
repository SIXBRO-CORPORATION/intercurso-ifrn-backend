from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.match.start_match_port import StartMatchPort
from core.context import Context
from domain.modality import Modality
from domain.modality_configuration import ModalityConfiguration
from domain.match_event import MatchEvent
from domain.team import Team
from domain.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_match_model_mapper,
    get_start_match_port,
    require_monitor,
)
from web.mappers.match_model_mapper import MatchModelMapper
from web.models.response.match_management_response import MatchManagementResponse

router = APIRouter(prefix="/api/match", tags=["match"])

# TODO (débito técnico Fase 5): endpoints de consulta (GET de partida por id,
# GET de partidas por temporada/time) e os demais casos de uso da fase
# (UC014 - Registrar Evento, UC015 - Finalizar Partida, UC017 - Corrigir
# Evento) ficam para as próximas rodadas desta fase, conforme o planejamento
# em docs/ai/planejamento.md.


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
