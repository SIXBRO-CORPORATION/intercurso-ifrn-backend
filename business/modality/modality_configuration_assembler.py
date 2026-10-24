from typing import Dict, List, Optional, Tuple
from uuid import UUID

from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)


async def attach_configurations(
    modalities: List[Modality],
    modality_configuration_repository: ModalityConfigurationRepositoryPort,
    volleyball_modality_configuration_repository: Optional[
        VolleyballModalityConfigurationRepositoryPort
    ] = None,
) -> Tuple[Dict[UUID, ModalityConfiguration], Dict[UUID, VolleyballModalityConfiguration]]:

    modality_ids = [m.id for m in modalities if m.id is not None]
    if not modality_ids:
        return {}, {}

    configurations = await modality_configuration_repository.find_by_modality_ids(
        modality_ids
    )
    configurations_by_modality = {
        configuration.modality_id: configuration for configuration in configurations
    }

    volleyball_by_modality: Dict[UUID, VolleyballModalityConfiguration] = {}
    if volleyball_modality_configuration_repository is not None:
        sets_configuration_ids = [
            configuration.id
            for configuration in configurations
            if configuration.score_type == ScoreType.SETS
            and configuration.id is not None
        ]
        if sets_configuration_ids:
            volleyball_configurations = (
                await volleyball_modality_configuration_repository.find_by_modality_configuration_ids(
                    sets_configuration_ids
                )
            )
            volleyball_by_configuration_id = {
                volleyball.modality_configuration_id: volleyball
                for volleyball in volleyball_configurations
            }
            volleyball_by_modality = {
                configuration.modality_id: volleyball_by_configuration_id[
                    configuration.id
                ]
                for configuration in configurations
                if configuration.id in volleyball_by_configuration_id
            }

    return configurations_by_modality, volleyball_by_modality
