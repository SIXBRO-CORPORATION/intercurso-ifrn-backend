import asyncio
import logging
from typing import Dict, Optional, Set

from core.messaging.push_sender_port import PushSenderPort
from core.messaging.season_broadcast_port import SeasonBroadcastPort
from domain.season.season import Season
from messaging.season_broadcast_content import (
    SEASON_TOPIC,
    registration_closed_content,
    registration_opened_content,
    registration_reopened_content,
    season_finished_content,
)

logger = logging.getLogger(__name__)


class SeasonBroadcastNotifier(SeasonBroadcastPort):

    def __init__(self, push_sender: PushSenderPort):
        self._push_sender = push_sender
        self._pending_tasks: Set[asyncio.Task] = set()

    async def registration_opened(self, season: Season) -> None:
        title, body = registration_opened_content(
            season.name, season.registration_end_date
        )
        self._dispatch(season, "registration_opened", title, body)

    async def registration_closed(self, season: Season) -> None:
        title, body = registration_closed_content(season.name)
        self._dispatch(season, "registration_closed", title, body)

    async def registration_reopened(self, season: Season) -> None:
        title, body = registration_reopened_content(
            season.name, season.registration_end_date
        )
        self._dispatch(season, "registration_reopened", title, body)

    async def season_finished(self, season: Season) -> None:
        title, body = season_finished_content(season.name)
        self._dispatch(season, "season_finished", title, body)

    def _dispatch(
        self, season: Season, event: str, title: str, body: str
    ) -> None:
        data: Dict[str, str] = {
            "season_id": str(season.id),
            "event": event,
        }
        task = asyncio.create_task(self._send(title, body, data))
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)

    async def _send(
        self, title: str, body: str, data: Optional[Dict[str, str]]
    ) -> None:
        try:
            await self._push_sender.send_to_topic(SEASON_TOPIC, title, body, data)
        except Exception:
            logger.exception(
                "Falha ao enviar push de broadcast de temporada (%s)",
                data.get("event") if data else "desconhecido",
            )
