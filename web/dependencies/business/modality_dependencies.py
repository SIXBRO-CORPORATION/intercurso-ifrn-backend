from typing import Annotated

from fastapi import Depends

from business.modality.create_modality_adapter import CreateModalityAdapter
from core.business.audit.audit_logger import AuditLogger
from core.business.modality.create_modality_port import CreateModalityPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.volleyball_modality_configuration_repository_port import \
    VolleyballModalityConfigurationRepositoryPort
from web.dependencies.commons_dependencies import get_audit_logger
from web.dependencies.persistence_dependencies import (
    get_modality_configuration_repository,
    get_modality_repository,
    get_volleyball_modality_configuration_repository,
)


def get_create_modality_port(
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> CreateModalityPort:
    return CreateModalityAdapter(
        modality_repository,
        modality_configuration_repository,
        audit_logger,
        volleyball_modality_configuration_repository,
    )
