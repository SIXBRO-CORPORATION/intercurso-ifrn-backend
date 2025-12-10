from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from core.context import Context

R = TypeVar('R')

class Command(ABC, Generic[R]):
    @abstractmethod
    async def execute(self, context: Context) -> R:
        pass