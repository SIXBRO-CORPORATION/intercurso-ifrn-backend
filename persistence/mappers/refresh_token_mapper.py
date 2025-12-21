from typing import Optional

from domain.refresh_token import RefreshToken
from persistence.model.refresh_token_entity import RefreshTokenEntity


class RefreshTokenMapper:
    def to_domain(self, entity: Optional[RefreshTokenEntity]) -> Optional[RefreshToken]:
        if entity is None:
            return None

        return RefreshToken(
            id=entity.id,
            user_id=entity.user_id,
            token=entity.token,
            expires_at=entity.expires_at,
            revoked=entity.revoked,
            revoked_at=entity.revoked_at,
            replaced_by_token=entity.replaced_by_token,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active,
        )

    def to_entity(self, domain: RefreshToken) -> RefreshTokenEntity:
        return RefreshTokenEntity(
            id=domain.id,
            user_id=domain.user_id,
            token=domain.token,
            expires_at=domain.expires_at,
            revoked=domain.revoked,
            revoked_at=domain.revoked_at,
            replaced_by_token=domain.replaced_by_token,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active,
        )
