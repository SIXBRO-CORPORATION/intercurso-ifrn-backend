from abc import ABC, abstractmethod
from typing import Optional

from domain.auth_token import SUAPUserData


class OAuthProviderPort(ABC):
    """
    Port (interface) para provedores OAuth2

    Esta é uma ABSTRAÇÃO que define o contrato.
    A implementação concreta (com httpx, requests, etc)
    fica em persistence/adapters/

    Princípio: Business não deve conhecer detalhes de HTTP!
    """

    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Gera URL de autorização do provedor OAuth2

        Args:
            state: String para prevenir CSRF

        Returns:
            URL completa para redirecionamento
        """
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> str:
        """
        Troca código de autorização por access_token

        Args:
            code: Código retornado após autorização

        Returns:
            Access token do provedor
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> SUAPUserData:
        """
        Busca informações do usuário usando access_token

        Args:
            access_token: Token do provedor

        Returns:
            Dados do usuário
        """
        pass

    @abstractmethod
    async def authenticate_with_code(self, code: str) -> SUAPUserData:
        """
        Fluxo completo: código → token → dados do usuário

        Args:
            code: Código de autorização

        Returns:
            Dados do usuário
        """
        pass