from typing import Optional

from domain.enums.device_platform import DevicePlatform
from domain.messaging.device_token import DeviceToken
from persistence.model.messaging.device_token_entity import DeviceTokenEntity


class DeviceTokenMapper:
    def to_domain(self, entity: Optional[DeviceTokenEntity]) -> Optional[DeviceToken]:
        if entity is None:
            return None

        return DeviceToken(
            id=entity.id,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            deleted_at=entity.deleted_at,
            active=entity.active,
            user_id=entity.user_id,
            token=entity.token,
            platform=DevicePlatform[entity.platform] if entity.platform else None,
            last_used_at=entity.last_used_at,
        )

    def to_entity(self, device_token: DeviceToken) -> DeviceTokenEntity:
        return DeviceTokenEntity(
            id=device_token.id,
            created_at=device_token.created_at,
            modified_at=device_token.modified_at,
            deleted_at=device_token.deleted_at,
            active=device_token.active,
            user_id=device_token.user_id,
            token=device_token.token,
            platform=device_token.platform.name if device_token.platform else None,
            last_used_at=device_token.last_used_at,
        )
