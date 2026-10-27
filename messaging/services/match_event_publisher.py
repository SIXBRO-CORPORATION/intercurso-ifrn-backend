import asyncio
from dataclasses import dataclass
from typing import Optional, Sequence

from core.messaging.push_sender_port import PushSenderPort
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.realtime.broadcaster import Broadcaster
from domain.enums.card_type import CardType
from domain.match.match import Match
from messaging.match_broadcast_content import BROADCAST_TOPIC, broadcast_push_content


@dataclass(frozen=True)
class MatchTeamSnapshot:

    name: str
    score: int


class MatchEventPublisher:

    def __init__(
        self,
        broadcaster: Broadcaster,
        push_sender: PushSenderPort,
        bracket_repository: BracketRepositoryPort,
    ):
        self._broadcaster = broadcaster
        self._push_sender = push_sender
        self._bracket_repository = bracket_repository

    async def publish(
        self,
        match: Match,
        event_types: str | Sequence[str],
        match_payload: Optional[dict] = None,
        team1: Optional[MatchTeamSnapshot] = None,
        team2: Optional[MatchTeamSnapshot] = None,
        card_type: Optional[CardType] = None,
    ) -> None:
        if isinstance(event_types, str):
            event_types = (event_types,)

        payload = {"match_id": str(match.id), "match": match_payload}

        for event_type in event_types:
            await self._broadcaster.publish(
                Broadcaster.match_channel(match.id),
                event_type,
                {**payload, "event": event_type},
            )

        if team1 is not None and team2 is not None:
            push_content = broadcast_push_content(
                event_types,
                team1.name,
                team2.name,
                team1.score,
                team2.score,
                card_type,
            )
            if push_content is not None:
                title, body = push_content
                asyncio.create_task(
                    self._push_sender.send_to_topic(
                        BROADCAST_TOPIC,
                        title,
                        body,
                        {"match_id": str(match.id), "event": event_types[0]},
                    )
                )

        if match.bracket_id is None:
            return

        bracket = await self._bracket_repository.get(match.bracket_id)
        if bracket is None or bracket.season_id is None:
            return

        for event_type in event_types:
            await self._broadcaster.publish(
                Broadcaster.season_channel(bracket.season_id),
                event_type,
                {**payload, "event": event_type},
            )
