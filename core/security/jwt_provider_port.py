from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Tuple
from uuid import UUID
from domain.auth_token import AuthToken
from domain.refresh_token import RefreshToken


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
    def create_refresh_token(self, user_id: UUID) -> RefreshToken:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict:
        pass

    @abstractmethod
    def hash_token(self, token: str) -> str:
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> UUID:
        pass

    @abstractmethod
    def create_token_pair(
            self,
            user_id: UUID,
            matricula: str,
            email: Optional[str] = None
    ) -> Tuple[AuthToken, str]:
        pass