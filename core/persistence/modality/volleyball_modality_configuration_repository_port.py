from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)


class VolleyballModalityConfigurationRepositoryPort(
    BaseRepositoryPort[VolleyballModalityConfiguration]
):
    @abstractmethod
    async def find_by_modality_configuration_id(
        self, modality_configuration_id: UUID
    ) -> Optional[VolleyballModalityConfiguration]:
        pass

    @abstractmethod
    async def find_by_modality_configuration_ids(
        self, modality_configuration_ids: List[UUID]
    ) -> List[VolleyballModalityConfiguration]:
        pass
