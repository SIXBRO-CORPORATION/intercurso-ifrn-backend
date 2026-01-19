from abc import abstractmethod
from typing import List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.modality import Modality


class ModalityRepositoryPort(BaseRepositoryPort[Modality]):
    @abstractmethod
    async def find_active_modalities(self) -> List[Modality]:
        pass

    @abstractmethod
    async def exists_by_id(self, modality_id: UUID) -> bool:
        pass