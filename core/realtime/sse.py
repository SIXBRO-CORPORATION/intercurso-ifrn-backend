"""Utilitários de streaming SSE, compartilhados entre os routers de tempo real.

Mantido em `core/realtime` (não em `web/`) porque a lógica de "como manter a
conexão viva, checar desconexão e formatar `event:`/`data:`" é a mesma para
qualquer canal (match, season, ...) �?" só o `channel` muda. Os routers em
`web/controllers` ficam responsáveis só por autenticação/autorização e por
montar o `channel` certo.
"""

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
    """Formata um RealtimeEvent no formato `event: <tipo>\\ndata: <json>\\n\\n`.

    Seção 4, cuidado #6: nunca concatenar string manualmente com dados não
    sanitizados �?" o payload é sempre serializado com um serializer JSON
    padrão (`json.dumps`), e cabe ao front tratar `data:` como JSON e
    escapar ao renderizar.
    """
    data = json.dumps(event.payload, default=str, ensure_ascii=False)
    return f"event: {event.event_type}\ndata: {data}\n\n"


def format_sse_comment(comment: str) -> str:
    """Formata uma linha de comentário SSE (ex.: heartbeat `: ping`)."""
    return f": {comment}\n\n"


async def stream_channel(
    request: Request,
    broadcaster: Broadcaster,
    channel: str,
    user_id: UUID,
) -> AsyncIterator[str]:
    """Gera o corpo de uma `StreamingResponse` para o canal informado.

    Assina o canal, emite cada evento publicado nele até a conexão do
    cliente cair, enviando heartbeats nos intervalos ociosos, e sempre
    desfaz a assinatura (`finally`) para não vazar a conexão no broadcaster.
    """
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
