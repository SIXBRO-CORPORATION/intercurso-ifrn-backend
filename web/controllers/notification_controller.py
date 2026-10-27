from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.messaging.register_device_token_port import RegisterDeviceTokenPort
from core.business.messaging.remove_device_token_port import RemoveDeviceTokenPort
from core.context import Context
from domain.enums.device_platform import DevicePlatform
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_register_device_token_port,
    get_remove_device_token_port,
    require_authenticated_user,
)
from web.models.request.messaging.register_device_token_request import (
    RegisterDeviceTokenRequest,
)
from web.models.request.messaging.remove_device_token_request import (
    RemoveDeviceTokenRequest,
)

router = APIRouter(prefix="/api/messaging", tags=["messaging"])


@router.post(
    "/device-token",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def register_device_token(
    request: RegisterDeviceTokenRequest,
    register_device_token_port: Annotated[
        RegisterDeviceTokenPort, Depends(get_register_device_token_port)
    ],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("user_id", current_user.id)
    context.put_property("token", request.token)
    context.put_property("platform", DevicePlatform[request.platform])

    device_token = await register_device_token_port.execute(context)

    return ApiResponse.success(
        data={
            "id": str(device_token.id),
            "platform": device_token.platform.value,
        },
        message="Dispositivo registrado para notificações",
    )


@router.delete(
    "/device-token",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def remove_device_token(
    request: RemoveDeviceTokenRequest,
    remove_device_token_port: Annotated[
        RemoveDeviceTokenPort, Depends(get_remove_device_token_port)
    ],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("user_id", current_user.id)
    context.put_property("token", request.token)

    await remove_device_token_port.execute(context)

    return ApiResponse.success(message="Dispositivo removido das notificações")
