from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional
from uuid import UUID

from domain.auth_token import AuthToken


class TokenServicePort(ABC):

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
        """
        Valida um token JWT

        Args:
            token: Token a ser validado

        Returns:
            Payload do token

        Raises:
            BusinessException: Se inválido
        """
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> UUID:
        """
        Extrai user_id do token

        Args:
            token: Token JWT

        Returns:
            UUID do usuário
        """
        pass

    @abstractmethod
    def refresh_token(self, old_token: str) -> AuthToken:
        """
        Renova um token

        Args:
            old_token: Token a renovar

        Returns:
            Novo token
        """
        pass