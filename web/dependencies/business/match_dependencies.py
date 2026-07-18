from typing import Annotated
from fastapi import Depends

from core.business.match.start_match_port import StartMatchPort
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from business.match.start_match_adapter import StartMatchAdapter
from web.dependencies.persistence_dependencies import (
    get_bracket_repository,
    get_match_event_repository,
    get_match_repository,
    get_modality_configuration_repository,
    get_modality_repository,
    get_team_member_repository,
    get_team_repository,
    get_user_repository,
)


def get_start_match_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
) -> StartMatchPort:
    return StartMatchAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_configuration_repository,
        modality_repository,
    )
