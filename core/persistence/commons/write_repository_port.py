from typing import TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar("T")


class WriteRepositoryPort(ABC, Generic[T]):
    @abstractmethod
    async def save(self, model: T):
        pass
