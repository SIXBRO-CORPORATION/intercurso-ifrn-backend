
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID

DEFAULT_QUEUE_MAX_SIZE = 100
DEFAULT_MAX_CONNECTIONS_PER_USER = 2


@dataclass(frozen=True)
class RealtimeEvent:

    event_type: str
    payload: dict
    published_at: float = field(default_factory=time.time)


class ConnectionLimitExceededError(Exception):
    pass


class Broadcaster:

    def __init__(
        self,
        queue_max_size: int = DEFAULT_QUEUE_MAX_SIZE,
        max_connections_per_user: int = DEFAULT_MAX_CONNECTIONS_PER_USER,
    ) -> None:
        self._queue_max_size = queue_max_size
        self._max_connections_per_user = max_connections_per_user

        self._channels: Dict[str, Set["asyncio.Queue[RealtimeEvent]"]] = defaultdict(set)
        self._connections_by_user: Dict[UUID, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    @staticmethod
    def match_channel(match_id: UUID) -> str:
        return f"match:{match_id}"

    @staticmethod
    def season_channel(season_id: UUID) -> str:
        return f"season:{season_id}"

    async def subscribe(
        self, channel: str, user_id: UUID
    ) -> "asyncio.Queue[RealtimeEvent]":
        async with self._lock:
            if self._connections_by_user[user_id] >= self._max_connections_per_user:
                raise ConnectionLimitExceededError(
                    f"Usuário {user_id} já possui o número máximo de conexões "
                    f"em tempo real permitidas ({self._max_connections_per_user})."
                )

            queue: "asyncio.Queue[RealtimeEvent]" = asyncio.Queue(
                maxsize=self._queue_max_size
            )
            self._channels[channel].add(queue)
            self._connections_by_user[user_id] += 1

            return queue

    async def unsubscribe(
        self, channel: str, user_id: UUID, queue: "asyncio.Queue[RealtimeEvent]"
    ) -> None:
        async with self._lock:
            self._channels[channel].discard(queue)
            if not self._channels[channel]:
                del self._channels[channel]

            if self._connections_by_user[user_id] > 0:
                self._connections_by_user[user_id] -= 1
            if self._connections_by_user[user_id] == 0:
                del self._connections_by_user[user_id]

    async def publish(self, channel: str, event_type: str, payload: dict) -> None:
        event = RealtimeEvent(event_type=event_type, payload=payload)

        async with self._lock:
            queues = list(self._channels.get(channel, ()))

        for queue in queues:
            self._put_discarding_oldest(queue, event)

    @staticmethod
    def _put_discarding_oldest(
        queue: "asyncio.Queue[RealtimeEvent]", event: RealtimeEvent
    ) -> None:
        while True:
            try:
                queue.put_nowait(event)
                return
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    continue

    def channel_subscriber_count(self, channel: str) -> int:
        return len(self._channels.get(channel, ()))


_broadcaster_instance: Broadcaster | None = None


def get_broadcaster_singleton() -> Broadcaster:
    global _broadcaster_instance
    if _broadcaster_instance is None:
        _broadcaster_instance = Broadcaster()
    return _broadcaster_instance
