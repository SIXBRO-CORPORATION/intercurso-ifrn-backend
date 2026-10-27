from uuid import UUID

from core.business.messaging.remove_device_token_port import RemoveDeviceTokenPort
from core.context import Context
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)
from domain.exceptions.business_exception import BusinessException


class RemoveDeviceTokenAdapter(RemoveDeviceTokenPort):
    def __init__(self, device_token_repository: DeviceTokenRepositoryPort):
        self.device_token_repository = device_token_repository

    async def execute(self, context: Context) -> None:
        user_id = context.get_property("user_id", UUID)
        token = context.get_property("token", str)

        if not token:
            raise BusinessException("Device token é obrigatório")


        existing = await self.device_token_repository.find_by_token(token)
        if existing is None or existing.user_id != user_id:
            return

        await self.device_token_repository.deactivate_by_token(token)
