from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from starlette.responses import StreamingResponse

from business.match._shared import load_management_context
from core.business.match.list_public_matches_port import ListPublicMatchesPort
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.match.match_set_repository_port import MatchSetRepositoryPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.modality.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.realtime.broadcaster import Broadcaster, ConnectionKey
from core.realtime.live_ticket_port import InvalidLiveTicketError, LiveTicketPort
from core.realtime.sse import stream_channel
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_bracket_repository,
    get_broadcaster,
    get_live_ticket_port,
    get_match_event_repository,
    get_match_repository,
    get_match_set_repository,
    get_modality_configuration_repository,
    get_modality_repository,
    get_team_member_repository,
    get_team_repository,
    get_user_repository,
    get_volleyball_modality_configuration_repository,
)
from web.dependencies.business.match_dependencies import get_list_public_matches_port
from web.dependencies.mapper_dependencies import get_match_model_mapper
from web.mappers.match_model_mapper import MatchModelMapper
from web.models.response.match.match_list_response import MatchListResponse
from web.models.response.match.match_public_response import MatchPublicResponse
from domain.enums.match_status import MatchStatus


def _connection_key(request: Request, user_id: UUID | None) -> ConnectionKey:
    if user_id is not None:
        return user_id
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"

router = APIRouter(prefix="/api/match", tags=["match-live"])

SSE_MEDIA_TYPE = "text/event-stream"
SSE_HEADERS = {
    "X-Accel-Buffering": "no",
    "Cache-Control": "no-cache",
}


@router.get("/", response_model=ApiResponse[MatchListResponse])
async def list_matches(
    list_port: Annotated[ListPublicMatchesPort, Depends(get_list_public_matches_port)],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
    season_id: UUID,
    modality_id: UUID | None = None,
    status: MatchStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):

    context = Context()
    for key, value in {
        "season_id": season_id,
        "modality_id": modality_id,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "page": page,
        "size": size,
    }.items():
        context.put_property(key, value)

    matches = await list_port.execute(context)

    return ApiResponse.success(
        data=mapper.to_list_response(
            matches,
            context.get("teams"),
            context.get("group_names"),
            context.get("bracket_modalities"),
            context.get("total"),
            context.get("page"),
            context.get("size"),
        )
    )


@router.get("/{match_id}/live")
async def stream_match_events(
    request: Request,
    match_id: UUID,
    ticket: Annotated[str, Query(description="Ticket emitido por POST /api/realtime/ticket")],
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    live_ticket_port: Annotated[LiveTicketPort, Depends(get_live_ticket_port)],
    broadcaster: Annotated[Broadcaster, Depends(get_broadcaster)],
):
    channel = Broadcaster.match_channel(match_id)

    try:
        user_id = live_ticket_port.verify_ticket(ticket, channel)
    except InvalidLiveTicketError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    match = await match_repository.get(match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partida não encontrada"
        )
    if match.status != MatchStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Canal ao vivo disponível apenas para partidas em andamento",
        )

    connection_key = _connection_key(request, user_id)

    return StreamingResponse(
        stream_channel(request, broadcaster, channel, connection_key),
        media_type=SSE_MEDIA_TYPE,
        headers=SSE_HEADERS,
    )


@router.get("/{match_id}", response_model=ApiResponse[MatchPublicResponse])
async def get_match_state(
    match_id: UUID,
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[ModalityRepositoryPort, Depends(get_modality_repository)],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
    mapper: Annotated[MatchModelMapper, Depends(get_match_model_mapper)],
):
    match = await match_repository.get(match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partida não encontrada"
        )
    context = Context()
    match.sync_clock()
    await load_management_context(
        context,
        match,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        match_event_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )
    response_data = mapper.to_management_response(
        match,
        context.get("team1"),
        context.get("team2"),
        context.get_property("team1_players", list) or [],
        context.get_property("team2_players", list) or [],
        context.get("modality"),
        context.get("modality_configuration"),
        context.get_property("timeline_events", list) or [],
        volleyball_configuration=context.get("volleyball_configuration"),
        match_sets=context.get_property("match_sets", list) or [],
    )
    public_data = MatchPublicResponse.model_validate(response_data)
    return ApiResponse.success(data=public_data)
