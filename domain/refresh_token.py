from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.abstract_domain import AbstractDomain


@dataclass
class RefreshToken(AbstractDomain):
    user_id: UUID = None
    token: str = None
    expires_at: datetime = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    replaced_by_token: Optional[UUID] = None

    def is_valid(self) -> bool:
        if self.revoked:
            return False

        if not self.active:
            return False

        if datetime.now() > self.expires_at:
            return False

        return True

    def revoke(self, replaced_by: Optional[UUID] = None) -> None:
        self.revoked = True
        self.revoked_at = datetime.now()
        self.replaced_by_token = replaced_by



