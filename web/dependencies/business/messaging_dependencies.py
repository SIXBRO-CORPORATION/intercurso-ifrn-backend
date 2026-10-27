from typing import Annotated

from fastapi import Depends

from business.messaging.register_device_token_adapter import (
    RegisterDeviceTokenAdapter,
)
from business.messaging.remove_device_token_adapter import RemoveDeviceTokenAdapter
from core.business.messaging.register_device_token_port import RegisterDeviceTokenPort
from core.business.messaging.remove_device_token_port import RemoveDeviceTokenPort
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)
from web.dependencies.persistence_dependencies import get_device_token_repository


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
