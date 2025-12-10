from typing import TypeVar, Generic, Optional, List
from abc import ABC, abstractmethod
from uuid import UUID

T = TypeVar('T')

class ReadRepositoryPort(ABC, Generic[T]):
    @abstractmethod
    def get(self, entity_id: UUID) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass