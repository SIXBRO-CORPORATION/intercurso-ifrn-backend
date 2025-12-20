from abc import abstractmethod
from typing import Optional

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.user import User


class UserRepositoryPort(BaseRepositoryPort[User]):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        pass

    @abstractmethod
    async def exists_by_matricula(self, matricula: int) -> bool:
        pass

    @abstractmethod
    async def find_by_matricula(self, matricula: int) -> Optional[User]:
        pass
