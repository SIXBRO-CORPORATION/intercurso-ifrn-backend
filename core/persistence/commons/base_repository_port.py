from typing import TypeVar
from abc import ABC

from core.persistence.commons.read_repository_port import ReadRepositoryPort
from core.persistence.commons.write_repository_port import WriteRepositoryPort

T = TypeVar("T")


class BaseRepositoryPort(ReadRepositoryPort[T], WriteRepositoryPort[T], ABC):
    pass
