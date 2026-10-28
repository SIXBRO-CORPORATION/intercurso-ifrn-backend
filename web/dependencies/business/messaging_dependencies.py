from typing import Annotated

from fastapi import Depends

from business.messaging.register_device_token_adapter import (
    RegisterDeviceTokenAdapter,
)
from business.messaging.remove_device_token_adapter import RemoveDeviceTokenAdapter
from core.business.messaging.register_device_token_port import RegisterDeviceTokenPort
from core.business.messaging.remove_device_token_port import RemoveDeviceTokenPort
from core.messaging.push_sender_port import PushSenderPort
from core.messaging.season_broadcast_port import SeasonBroadcastPort
from core.messaging.team_notification_port import TeamNotificationPort
from messaging.services.personal_notifier import PersonalNotifier
from messaging.services.season_broadcast_notifier import SeasonBroadcastNotifier
from messaging.services.team_notification_notifier import TeamNotificationNotifier
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


def get_personal_notifier(
    device_token_repository: Annotated[
        DeviceTokenRepositoryPort, Depends(get_device_token_repository)
    ],
    push_sender: Annotated[PushSenderPort, Depends(get_push_sender)],
) -> PersonalNotifier:
    return PersonalNotifier(
        device_token_repository=device_token_repository,
        push_sender=push_sender,
    )


def get_season_broadcast_notifier(
    push_sender: Annotated[PushSenderPort, Depends(get_push_sender)],
) -> SeasonBroadcastPort:
    return SeasonBroadcastNotifier(push_sender=push_sender)


def get_team_notification_port(
    personal_notifier: Annotated[PersonalNotifier, Depends(get_personal_notifier)],
) -> TeamNotificationPort:
    return TeamNotificationNotifier(personal_notifier=personal_notifier)
