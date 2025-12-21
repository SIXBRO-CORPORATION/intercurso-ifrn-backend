from abc import ABC, abstractmethod
from typing import Optional
from domain.user import User


class OAuthProviderPort(ABC):
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> User:
        pass

    @abstractmethod
    async def authenticate_with_code(self, code: str) -> User:
        pass


class SuapOAuthPort:
    pass
