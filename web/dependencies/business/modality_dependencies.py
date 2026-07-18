from typing import Annotated

from fastapi import Depends

from business.modality.create_modality_adapter import CreateModalityAdapter
from core.business.modality.create_modality_port import CreateModalityPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from web.dependencies.persistence_dependencies import (
    get_modality_configuration_repository,
    get_modality_repository,
)


def get_create_modality_port(
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
) -> CreateModalityPort:
    return CreateModalityAdapter(
        modality_repository, modality_configuration_repository
    )
