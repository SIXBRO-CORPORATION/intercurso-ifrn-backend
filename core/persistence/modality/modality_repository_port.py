from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.modality.modality import Modality


class ModalityRepositoryPort(BaseRepositoryPort[Modality]):
    @abstractmethod
    async def find_active_modalities(self) -> List[Modality]:
        pass

    @abstractmethod
    async def exists_by_id(self, modality_id: UUID) -> bool:
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Modality]:
        pass