from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.realtime.broadcaster import Broadcaster
from core.realtime.live_ticket_port import LiveTicketPort
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_live_ticket_port,
    get_match_repository,
    get_season_repository,
    require_authenticated_user,
)
from web.models.request.realtime.live_ticket_request import (
    LiveChannelType,
    LiveTicketRequest,
)
from web.models.response.realtime.live_ticket_response import LiveTicketResponse
from security.adapters.live_ticket_adapter import DEFAULT_TICKET_TTL_SECONDS
from domain.enums.match_status import MatchStatus

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

TICKET_TTL_SECONDS = DEFAULT_TICKET_TTL_SECONDS


@router.post(
    "/ticket",
    response_model=ApiResponse[LiveTicketResponse],
    status_code=status.HTTP_200_OK,
)
async def issue_live_ticket(
    request: LiveTicketRequest,
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    live_ticket_port: Annotated[LiveTicketPort, Depends(get_live_ticket_port)],
    current_user: User = Depends(require_authenticated_user),
):
    if request.channel_type == LiveChannelType.MATCH:
        match = await match_repository.get(request.channel_id)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Partida não encontrada"
            )
        if match.status != MatchStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Só é possível abrir canal ao vivo para partidas em andamento",
            )
        channel = Broadcaster.match_channel(request.channel_id)

    ticket = live_ticket_port.issue_ticket(current_user.id, channel)

    return ApiResponse(
        data=LiveTicketResponse(ticket=ticket, expires_in_seconds=TICKET_TTL_SECONDS),
        message="Ticket emitido com sucesso",
    )
