from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.messaging.register_device_token_adapter import (
    RegisterDeviceTokenAdapter,
)
from core.context import Context
from domain.enums.device_platform import DevicePlatform
from domain.exceptions.business_exception import BusinessException
from domain.messaging.device_token import DeviceToken


def make_context(user_id=None, token="token-abc", platform=DevicePlatform.ANDROID):
    context = Context()
    if user_id is not None:
        context.put_property("user_id", user_id)
    context.put_property("token", token)
    context.put_property("platform", platform)
    return context


@pytest.mark.unit
class TestRegisterDeviceTokenAdapter:
    @pytest.mark.asyncio
    async def test_registers_new_token(self):
        repository = AsyncMock()
        repository.find_by_token.return_value = None
        repository.save.side_effect = lambda device_token: device_token
        adapter = RegisterDeviceTokenAdapter(repository)

        user_id = uuid4()
        context = make_context(user_id=user_id, token="new-token")

        result = await adapter.execute(context)

        assert isinstance(result, DeviceToken)
        assert result.user_id == user_id
        assert result.token == "new-token"
        assert result.platform == DevicePlatform.ANDROID
        assert result.active is True
        assert result.last_used_at is not None
        repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reactivates_and_reassigns_existing_token(self):
        repository = AsyncMock()
        previous_owner = uuid4()
        existing = DeviceToken(
            id=uuid4(),
            user_id=previous_owner,
            token="shared-token",
            platform=DevicePlatform.IOS,
            active=False,
        )
        repository.find_by_token.return_value = existing
        repository.save.side_effect = lambda device_token: device_token
        adapter = RegisterDeviceTokenAdapter(repository)

        new_owner = uuid4()
        context = make_context(
            user_id=new_owner, token="shared-token", platform=DevicePlatform.ANDROID
        )

        result = await adapter.execute(context)

        # device reinstalado/trocado de dono: o token existente é
        # realocado para o novo usuário, não duplicado.
        assert result is existing
        assert result.user_id == new_owner
        assert result.platform == DevicePlatform.ANDROID
        assert result.active is True

    @pytest.mark.asyncio
    async def test_raises_when_user_id_is_missing(self):
        repository = AsyncMock()
        adapter = RegisterDeviceTokenAdapter(repository)

        context = make_context(user_id=None)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_token_is_blank(self):
        repository = AsyncMock()
        repository.find_by_token.return_value = None
        adapter = RegisterDeviceTokenAdapter(repository)

        context = make_context(token="")

        with pytest.raises(BusinessException):
            await adapter.execute(context)
