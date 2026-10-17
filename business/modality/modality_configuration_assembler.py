from typing import Dict, List
from uuid import UUID

from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


async def attach_configurations(
    modalities: List[Modality],
    modality_configuration_repository: ModalityConfigurationRepositoryPort,
) -> Dict[UUID, ModalityConfiguration]:

    modality_ids = [m.id for m in modalities if m.id is not None]
    if not modality_ids:
        return {}

    configurations = await modality_configuration_repository.find_by_modality_ids(
        modality_ids
    )
    return {
        configuration.modality_id: configuration for configuration in configurations
    }
