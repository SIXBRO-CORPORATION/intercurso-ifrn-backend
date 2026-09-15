"""Broadcaster em memória para o canal de tempo real (UC016).

Implementa o componente descrito na seção 2.1 da solução técnica vinculada ao
ADR 0003: um mapa `canal -> lista de filas (asyncio.Queue)`, onde cada
`match_id` e cada `season_id` é um canal.

Este componente é infraestrutura pura (sem regra de negócio) e vive em
`core/` porque é compartilhado entre domínios (`business/match`,
`business/season`, ...). Ele N�fO sabe nada sobre HTTP/SSE �?" quem formata a
resposta como `event: ...\ndata: ...\n\n` é o router (`web/controllers`).

Limitações conhecidas e assumidas (ver seção 3 da solução técnica):
- Não funciona com múltiplas instâncias/workers (sem Redis Pub/Sub). Cada
  worker Uvicorn tem seu próprio broadcaster isolado. Documentado, não é bug.
- Um cliente lento nunca pode travar a escrita de outro usuário: por isso a
  fila tem tamanho máximo e descarta a mensagem mais antiga quando cheia,
  em vez de bloquear `publish`.
"""

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
    """Envelope de um evento publicado no broadcaster."""

    event_type: str
    payload: dict
    published_at: float = field(default_factory=time.time)


class ConnectionLimitExceededError(Exception):
    """Levantada quando um usuário já atingiu o limite de conexões SSE simultâneas."""


class Broadcaster:
    """Publica/assina eventos em memória, por canal.

    Um "canal" é uma string opaca para este componente (ex.: `match:<uuid>`,
    `season:<uuid>`) �?" quem decide o formato do nome do canal é quem publica
    e quem assina, não o broadcaster.
    """

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
        """Registra uma nova conexão SSE no canal.

        Levanta `ConnectionLimitExceededError` se o usuário já tiver atingido
        o limite de conexões simultâneas (cuidado de segurança #3 da seção 4:
        evitar exaustão de recursos por um `EventSource` mal comportado).
        """
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
        """Remove a fila do canal quando a conexão SSE cai/fecha.

        Deve sempre ser chamado em um `finally` no router, ou a conexão fica
        "vazando" no broadcaster mesmo depois do cliente desconectar.
        """
        async with self._lock:
            self._channels[channel].discard(queue)
            if not self._channels[channel]:
                del self._channels[channel]

            if self._connections_by_user[user_id] > 0:
                self._connections_by_user[user_id] -= 1
            if self._connections_by_user[user_id] == 0:
                del self._connections_by_user[user_id]

    async def publish(self, channel: str, event_type: str, payload: dict) -> None:
        """Envia o evento para todas as filas registradas naquele canal.

        Chamado pelos Commands/routers de escrita depois de persistir com
        sucesso (Opção A da seção 2.2: publicação no router). Nunca bloqueia:
        se uma fila estiver cheia, descarta a mensagem mais antiga e insere a
        nova no lugar (política de descarte da seção 3/4.4) �?" um consumidor
        lento não pode atrasar quem está publicando.
        """
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
        """Utilitário para testes/observabilidade: quantas conexões ativas num canal."""
        return len(self._channels.get(channel, ()))


_broadcaster_instance: Broadcaster | None = None


def get_broadcaster_singleton() -> Broadcaster:
    global _broadcaster_instance
    if _broadcaster_instance is None:
        _broadcaster_instance = Broadcaster()
    return _broadcaster_instance
