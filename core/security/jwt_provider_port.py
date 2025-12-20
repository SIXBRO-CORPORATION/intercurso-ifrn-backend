from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional
from uuid import UUID

from domain.auth_token import AuthToken


class JWTProviderPort(ABC):

    @abstractmethod
    def create_access_token(
            self,
            user_id: UUID,
            matricula: str,
            email: Optional[str] = None,
            expires_delta: Optional[timedelta] = None
    ) -> AuthToken:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict:
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> UUID:

        pass

    @abstractmethod
    def refresh_token(self, old_token: str) -> AuthToken:

        pass