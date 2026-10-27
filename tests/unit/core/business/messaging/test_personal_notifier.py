import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from messaging.services.personal_notifier import PersonalNotifier
from domain.enums.device_platform import DevicePlatform
from domain.messaging.device_token import DeviceToken
from domain.messaging.push_send_result import PushSendResult


def make_device_token(user_id, token) -> DeviceToken:
    return DeviceToken(
        id=uuid4(), user_id=user_id, token=token, platform=DevicePlatform.ANDROID
    )


def make_notifier():
    device_token_repository = AsyncMock()
    push_sender = AsyncMock()
    notifier = PersonalNotifier(
        device_token_repository=device_token_repository,
        push_sender=push_sender,
    )
    return notifier, device_token_repository, push_sender


@pytest.mark.unit
class TestPersonalNotifier:
    @pytest.mark.asyncio
    async def test_notify_user_sends_to_all_active_tokens_of_the_user(self):
        notifier, device_token_repository, push_sender = make_notifier()
        user_id = uuid4()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(user_id, "token-1"),
            make_device_token(user_id, "token-2"),
        ]
        push_sender.send.return_value = PushSendResult(success_count=2)

        await notifier.notify_user(
            user_id, "Seu time foi aprovado!", "Boa sorte na competição.", {"k": "v"}
        )
        await asyncio.sleep(0)  # cede o loop pra fire-and-forget task rodar

        device_token_repository.find_active_by_users.assert_awaited_once_with(
            [user_id]
        )
        push_sender.send.assert_awaited_once_with(
            ["token-1", "token-2"],
            "Seu time foi aprovado!",
            "Boa sorte na competição.",
            {"k": "v"},
        )

    @pytest.mark.asyncio
    async def test_notify_users_resolves_tokens_for_every_recipient(self):
        notifier, device_token_repository, push_sender = make_notifier()
        user1, user2 = uuid4(), uuid4()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(user1, "token-1"),
            make_device_token(user2, "token-2"),
        ]
        push_sender.send.return_value = PushSendResult(success_count=2)

        await notifier.notify_users([user1, user2], "Título", "Corpo")
        await asyncio.sleep(0)

        device_token_repository.find_active_by_users.assert_awaited_once_with(
            [user1, user2]
        )
        push_sender.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_notify_users_is_noop_when_no_recipients(self):
        notifier, device_token_repository, push_sender = make_notifier()

        await notifier.notify_users([], "Título", "Corpo")
        await asyncio.sleep(0)

        device_token_repository.find_active_by_users.assert_not_called()
        push_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_users_filters_out_none_user_ids(self):
        notifier, device_token_repository, push_sender = make_notifier()
        user_id = uuid4()
        device_token_repository.find_active_by_users.return_value = []

        await notifier.notify_users([user_id, None], "Título", "Corpo")
        await asyncio.sleep(0)

        device_token_repository.find_active_by_users.assert_awaited_once_with(
            [user_id]
        )
        push_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_call_push_sender_when_user_has_no_active_tokens(self):
        notifier, device_token_repository, push_sender = make_notifier()
        device_token_repository.find_active_by_users.return_value = []

        await notifier.notify_user(uuid4(), "Título", "Corpo")
        await asyncio.sleep(0)

        push_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivates_tokens_reported_as_invalid_by_fcm(self):
        notifier, device_token_repository, push_sender = make_notifier()
        user_id = uuid4()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(user_id, "valid-token"),
            make_device_token(user_id, "stale-token"),
        ]
        push_sender.send.return_value = PushSendResult(
            success_count=1, failure_count=1, invalid_tokens=["stale-token"]
        )

        await notifier.notify_user(user_id, "Título", "Corpo")
        await asyncio.sleep(0)

        device_token_repository.deactivate_by_token.assert_awaited_once_with(
            "stale-token"
        )

    @pytest.mark.asyncio
    async def test_does_not_deactivate_anything_when_no_invalid_tokens(self):
        notifier, device_token_repository, push_sender = make_notifier()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(uuid4(), "token-1")
        ]
        push_sender.send.return_value = PushSendResult(success_count=1)

        await notifier.notify_user(uuid4(), "Título", "Corpo")
        await asyncio.sleep(0)

        device_token_repository.deactivate_by_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_swallows_push_sender_failure_without_raising(self):
        notifier, device_token_repository, push_sender = make_notifier()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(uuid4(), "token-1")
        ]
        push_sender.send.side_effect = RuntimeError("FCM indisponível")

        # Não deve propagar: quem chamou (um adapter de negócio) não
        # pode ter seu fluxo principal derrubado por falha de push.
        await notifier.notify_user(uuid4(), "Título", "Corpo")
        await asyncio.sleep(0)

    @pytest.mark.asyncio
    async def test_swallows_repository_failure_without_raising(self):
        notifier, device_token_repository, push_sender = make_notifier()
        device_token_repository.find_active_by_users.side_effect = RuntimeError(
            "banco indisponível"
        )

        await notifier.notify_user(uuid4(), "Título", "Corpo")
        await asyncio.sleep(0)

        push_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_does_not_block_caller_on_slow_send(self):
        # O disparo é fire-and-forget (asyncio.create_task): notify_user
        # deve retornar antes do push_sender.send terminar.
        notifier, device_token_repository, push_sender = make_notifier()
        device_token_repository.find_active_by_users.return_value = [
            make_device_token(uuid4(), "token-1")
        ]

        send_started = asyncio.Event()

        async def slow_send(*args, **kwargs):
            send_started.set()
            await asyncio.sleep(10)
            return PushSendResult(success_count=1)

        push_sender.send.side_effect = slow_send

        await asyncio.wait_for(
            notifier.notify_user(uuid4(), "Título", "Corpo"), timeout=0.5
        )
        assert not send_started.is_set()
