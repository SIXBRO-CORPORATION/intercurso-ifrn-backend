from typing import Annotated

from fastapi import Depends

from business.season.close_registration_adapter import CloseRegistrationAdapter
from business.season.create_season_adapter import CreateSeasonAdapter
from business.season.finish_season_adapter import FinishSeasonAdapter
from business.season.get_season_details_adapter import GetSeasonDetailsAdapter
from business.season.manage_season_adapter import ManageSeasonAdapter
from business.season.reopen_registration_adapter import ReopenRegistrationAdapter
from core.business.audit.audit_logger import AuditLogger
from core.business.season.close_registration_port import CloseRegistrationPort
from core.business.season.create_season_port import CreateSeasonPort
from core.business.season.finish_season_port import FinishSeasonPort
from core.business.season.get_season_details_port import GetSeasonDetailsPort
from core.business.season.manage_season_port import ManageSeasonPort
from core.business.season.reopen_registration_port import ReopenRegistrationPort
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from web.dependencies.commons_dependencies import get_audit_logger
from web.dependencies.persistence_dependencies import (
    get_modality_repository,
    get_season_modality_repository,
    get_season_repository,
    get_team_repository,
    get_user_repository,
)


def get_create_season_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> CreateSeasonPort:
    return CreateSeasonAdapter(
        season_repository,
        season_modality_repository,
        modality_repository,
        user_repository,
        audit_logger,
    )


def get_manage_season_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> ManageSeasonPort:
    return ManageSeasonAdapter(season_repository, user_repository, audit_logger)


def get_close_registration_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> CloseRegistrationPort:
    return CloseRegistrationAdapter(season_repository, user_repository, audit_logger)


def get_reopen_registration_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> ReopenRegistrationPort:
    return ReopenRegistrationAdapter(season_repository, user_repository, audit_logger)


def get_finish_season_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> FinishSeasonPort:
    return FinishSeasonAdapter(
        season_repository, team_repository, user_repository, audit_logger
    )


def get_season_details_port(
    season_repository: Annotated[
        SeasonRepositoryPort, Depends(get_season_repository)
    ],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
) -> GetSeasonDetailsPort:
    return GetSeasonDetailsAdapter(
        season_repository, season_modality_repository, team_repository
    )