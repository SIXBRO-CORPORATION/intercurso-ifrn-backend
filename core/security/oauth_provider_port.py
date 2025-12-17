from abc import ABC, abstractmethod
from typing import Optional
from domain.auth_token import SUAPUserData


class OAuthProviderPort(ABC):

    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> SUAPUserData:
        pass

    @abstractmethod
    async def authenticate_with_code(self, code: str) -> SUAPUserData:
        pass