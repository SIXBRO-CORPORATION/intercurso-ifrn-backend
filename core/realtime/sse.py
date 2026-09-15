
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator
from uuid import UUID

from fastapi import Request

from core.realtime.broadcaster import (
    Broadcaster,
    ConnectionLimitExceededError,
    RealtimeEvent,
)

HEARTBEAT_INTERVAL_SECONDS = 15


def format_sse_message(event: RealtimeEvent) -> str:
    data = json.dumps(event.payload, default=str, ensure_ascii=False)
    return f"event: {event.event_type}\ndata: {data}\n\n"


def format_sse_comment(comment: str) -> str:
    return f": {comment}\n\n"


async def stream_channel(
    request: Request,
    broadcaster: Broadcaster,
    channel: str,
    user_id: UUID,
) -> AsyncIterator[str]:
    try:
        queue = await broadcaster.subscribe(channel, user_id)
    except ConnectionLimitExceededError as exc:
        yield format_sse_message(
            RealtimeEvent(event_type="error", payload={"detail": str(exc)})
        )
        return

    try:
        while True:
            if await request.is_disconnected():
                break

            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=HEARTBEAT_INTERVAL_SECONDS
                )
                yield format_sse_message(event)
            except asyncio.TimeoutError:
                yield format_sse_comment("ping")
    finally:
        await broadcaster.unsubscribe(channel, user_id, queue)
