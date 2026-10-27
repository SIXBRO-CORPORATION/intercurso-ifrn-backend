from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.messaging.remove_device_token_adapter import RemoveDeviceTokenAdapter
from core.context import Context
from domain.enums.device_platform import DevicePlatform
from domain.exceptions.business_exception import BusinessException
from domain.messaging.device_token import DeviceToken


def make_context(user_id=None, token="token-abc"):
    context = Context()
    if user_id is not None:
        context.put_property("user_id", user_id)
    context.put_property("token", token)
    return context


@pytest.mark.unit
class TestRemoveDeviceTokenAdapter:
    @pytest.mark.asyncio
    async def test_deactivates_token_owned_by_the_user(self):
        repository = AsyncMock()
        user_id = uuid4()
        repository.find_by_token.return_value = DeviceToken(
            id=uuid4(),
            user_id=user_id,
            token="token-abc",
            platform=DevicePlatform.ANDROID,
        )
        adapter = RemoveDeviceTokenAdapter(repository)

        context = make_context(user_id=user_id, token="token-abc")

        await adapter.execute(context)

        repository.deactivate_by_token.assert_awaited_once_with("token-abc")

    @pytest.mark.asyncio
    async def test_is_noop_when_token_does_not_exist(self):
        repository = AsyncMock()
        repository.find_by_token.return_value = None
        adapter = RemoveDeviceTokenAdapter(repository)

        context = make_context(user_id=uuid4(), token="unknown-token")

        await adapter.execute(context)

        repository.deactivate_by_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_noop_when_token_belongs_to_another_user(self):
        # Não vaza se o token existe ou não: usuário não pode remover
        # device token de outro usuário, e o retorno é o mesmo de
        # "não encontrado" (sem levantar erro de permissão).
        repository = AsyncMock()
        owner_id = uuid4()
        requester_id = uuid4()
        repository.find_by_token.return_value = DeviceToken(
            id=uuid4(),
            user_id=owner_id,
            token="token-abc",
            platform=DevicePlatform.ANDROID,
        )
        adapter = RemoveDeviceTokenAdapter(repository)

        context = make_context(user_id=requester_id, token="token-abc")

        await adapter.execute(context)

        repository.deactivate_by_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_token_is_blank(self):
        repository = AsyncMock()
        adapter = RemoveDeviceTokenAdapter(repository)

        context = make_context(token="")

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        repository.find_by_token.assert_not_called()
