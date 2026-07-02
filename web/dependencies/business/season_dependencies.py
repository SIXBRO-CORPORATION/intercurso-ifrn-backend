from typing import Annotated

from fastapi import Depends

from business.season.create_season_adapter import CreateSeasonAdapter
from core.business.season.create_season_port import CreateSeasonPort
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season_repository_port import SeasonRepositoryPort
from web.dependencies.persistence_dependencies import (
    get_modality_repository,
    get_season_modality_repository,
    get_season_repository,
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
) -> CreateSeasonPort:
    return CreateSeasonAdapter(
        season_repository, season_modality_repository, modality_repository
    )
