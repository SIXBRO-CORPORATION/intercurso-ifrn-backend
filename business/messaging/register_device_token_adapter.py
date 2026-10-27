from uuid import UUID

from core.business.messaging.register_device_token_port import RegisterDeviceTokenPort
from core.context import Context
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)
from domain.enums.device_platform import DevicePlatform
from domain.exceptions.business_exception import BusinessException
from domain.messaging.device_token import DeviceToken


class RegisterDeviceTokenAdapter(RegisterDeviceTokenPort):
    def __init__(self, device_token_repository: DeviceTokenRepositoryPort):
        self.device_token_repository = device_token_repository

    async def execute(self, context: Context) -> DeviceToken:
        user_id = context.get_property("user_id", UUID)
        token = context.get_property("token", str)
        platform = context.get_property("platform", DevicePlatform)

        if user_id is None:
            raise BusinessException("Usuário é obrigatório")

        existing = await self.device_token_repository.find_by_token(token)
        if existing is not None:
            existing.user_id = user_id
            existing.platform = platform
            existing.active = True
            existing.validate()
            existing.touch()
            return await self.device_token_repository.save(existing)

        device_token = DeviceToken(user_id=user_id, token=token, platform=platform)
        device_token.validate()
        device_token.touch()

        return await self.device_token_repository.save(device_token)
