from typing import TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')

class WriteRepositoryPort(ABC, Generic[T]):
    @abstractmethod
    def save(self, model: T):
        pass