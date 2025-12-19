from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from domain.exceptions.business_exception import BusinessException
from domain.abstract_domain import AbstractDomain


@dataclass
class RefreshToken(AbstractDomain):
    user_id: UUID = None
    token: str = None
    expires_at: datetime = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    replaced_by_token: Optional[UUID] = None

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        if self.revoked:
            return False

        if not self.active:
            return False

        if datetime.now() > self.expires_at:
            return False

        return True

    def validate(self) -> None:
        if self.revoked:
            raise BusinessException("Refresh token foi revogado")

        if not self.active:
            raise BusinessException("Refresh token está inativo")

        if self.is_expired():
            raise BusinessException("Refresh token expirado")

    def revoke(self, replaced_by: Optional[UUID] = None) -> None:
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.replaced_by_token = replaced_by

    def rotate(self, new_token_id: UUID) -> None:
        self.revoke(replaced_by=new_token_id)

