import asyncio
import logging
from typing import Dict, Iterable, Optional, Set
from uuid import UUID

from core.messaging.push_sender_port import PushSenderPort
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)

logger = logging.getLogger(__name__)


class PersonalNotifier:

    def __init__(
        self,
        device_token_repository: DeviceTokenRepositoryPort,
        push_sender: PushSenderPort,
    ):
        self._device_token_repository = device_token_repository
        self._push_sender = push_sender
        self._pending_tasks: Set[asyncio.Task] = set()

    async def notify_user(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> None:
        await self.notify_users((user_id,), title, body, data)

    async def notify_users(
        self,
        user_ids: Iterable[UUID],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> None:
        resolved_user_ids = [user_id for user_id in user_ids if user_id is not None]
        if not resolved_user_ids:
            return

        task = asyncio.create_task(
            self._dispatch(resolved_user_ids, title, body, data)
        )
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)

    async def _dispatch(
        self,
        user_ids: list,
        title: str,
        body: str,
        data: Optional[Dict[str, str]],
    ) -> None:
        try:
            device_tokens = await self._device_token_repository.find_active_by_users(
                user_ids
            )
            tokens = [device_token.token for device_token in device_tokens]
            if not tokens:
                return

            result = await self._push_sender.send(tokens, title, body, data)

            for invalid_token in result.invalid_tokens:
                await self._device_token_repository.deactivate_by_token(
                    invalid_token
                )
        except Exception:
            logger.exception(
                "Falha ao enviar push notification dirigida para %d destinatário(s)",
                len(user_ids),
            )
