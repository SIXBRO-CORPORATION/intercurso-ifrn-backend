from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.refresh_token import RefreshToken


class RefreshTokenRepositoryPort(BaseRepositoryPort[RefreshToken]):
    @abstractmethod
    async def find_by_token(self, token: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    async def find_active_by_user(self, user_id: UUID) -> List[RefreshToken]:
        pass

    @abstractmethod
    async def revoke_all_by_user(self, user_id: UUID) -> int:
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        pass

    async def count_active_by_user(self, user_id: UUID) -> int:
        tokens = await self.find_active_by_user(user_id)
        return len(tokens)

    async def revoke_token_by_id(self, token_id: UUID) -> bool:
        token = await self.get(token_id)
        if token and not token.revoked:
            token.revoke()
            await self.save(token)
            return True
        return False
