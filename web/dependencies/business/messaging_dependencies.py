from typing import Annotated

from fastapi import Depends

from business.messaging.register_device_token_adapter import (
    RegisterDeviceTokenAdapter,
)
from business.messaging.remove_device_token_adapter import RemoveDeviceTokenAdapter
from core.business.messaging.register_device_token_port import RegisterDeviceTokenPort
from core.business.messaging.remove_device_token_port import RemoveDeviceTokenPort
from core.messaging.push_sender_port import PushSenderPort
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)
from messaging.adapters.fcm_push_sender_adapter import FCMPushSenderAdapter
from web.dependencies.persistence_dependencies import get_device_token_repository


def get_push_sender() -> PushSenderPort:
    return FCMPushSenderAdapter()


def get_register_device_token_port(
    device_token_repository: Annotated[
        DeviceTokenRepositoryPort, Depends(get_device_token_repository)
    ],
) -> RegisterDeviceTokenPort:
    return RegisterDeviceTokenAdapter(device_token_repository)


def get_remove_device_token_port(
    device_token_repository: Annotated[
        DeviceTokenRepositoryPort, Depends(get_device_token_repository)
    ],
) -> RemoveDeviceTokenPort:
    return RemoveDeviceTokenAdapter(device_token_repository)
