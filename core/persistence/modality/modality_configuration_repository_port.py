from abc import abstractmethod
from typing import Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.modality.modality_configuration import ModalityConfiguration


class ModalityConfigurationRepositoryPort(BaseRepositoryPort[ModalityConfiguration]):
    @abstractmethod
    async def find_by_modality(
        self, modality_id: UUID
    ) -> Optional[ModalityConfiguration]:
        pass

    @abstractmethod
    async def exists_by_modality(self, modality_id: UUID) -> bool:
        pass