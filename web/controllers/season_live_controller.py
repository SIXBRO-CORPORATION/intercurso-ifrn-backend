from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from starlette.responses import StreamingResponse

from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.realtime.broadcaster import Broadcaster
from core.realtime.live_ticket_port import InvalidLiveTicketError, LiveTicketPort
from core.realtime.sse import stream_channel
from web.controllers.match_live_controller import SSE_HEADERS, SSE_MEDIA_TYPE
from web.dependencies import get_broadcaster, get_live_ticket_port, get_season_repository

router = APIRouter(prefix="/api/season", tags=["season-live"])


@router.get("/{season_id}/live")
async def stream_season_events(
    request: Request,
    season_id: UUID,
    ticket: Annotated[str, Query(description="Ticket emitido por POST /api/realtime/ticket")],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    live_ticket_port: Annotated[LiveTicketPort, Depends(get_live_ticket_port)],
    broadcaster: Annotated[Broadcaster, Depends(get_broadcaster)],
):
    channel = Broadcaster.season_channel(season_id)

    try:
        user_id = live_ticket_port.verify_ticket(ticket, channel)
    except InvalidLiveTicketError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    season = await season_repository.get(season_id)
    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Temporada não encontrada"
        )

    return StreamingResponse(
        stream_channel(request, broadcaster, channel, user_id),
        media_type=SSE_MEDIA_TYPE,
        headers=SSE_HEADERS,
    )
