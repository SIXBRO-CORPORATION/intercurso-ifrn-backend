from typing import Annotated
from fastapi import Depends

from core.business.bracket.create_bracket_port import CreateBracketPort
from core.business.bracket.delete_match_port import DeleteMatchPort
from core.business.bracket.get_bracket_config_suggestion_port import (
    GetBracketConfigSuggestionPort,
)
from core.business.bracket.resort_bracket_port import ResortBracketPort
from core.business.bracket.update_match_port import UpdateMatchPort
from core.persistence.bracket.bracket_group_repository_port import BracketGroupRepositoryPort
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from business.bracket.create_bracket_adapter import CreateBracketAdapter
from business.bracket.delete_match_adapter import DeleteMatchAdapter
from business.bracket.get_bracket_config_suggestion_adapter import (
    GetBracketConfigSuggestionAdapter,
)
from business.bracket.resort_bracket_adapter import ResortBracketAdapter
from business.bracket.update_match_adapter import UpdateMatchAdapter
from web.dependencies.persistence_dependencies import (
    get_bracket_group_repository,
    get_bracket_group_team_repository,
    get_bracket_repository,
    get_match_repository,
    get_season_modality_repository,
    get_season_repository,
    get_team_repository,
)


def get_bracket_config_suggestion_port(
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
) -> GetBracketConfigSuggestionPort:
    return GetBracketConfigSuggestionAdapter(
        season_repository,
        season_modality_repository,
        team_repository,
        bracket_repository,
    )


def get_create_bracket_port(
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    bracket_group_repository: Annotated[
        BracketGroupRepositoryPort, Depends(get_bracket_group_repository)
    ],
    bracket_group_team_repository: Annotated[
        BracketGroupTeamRepositoryPort, Depends(get_bracket_group_team_repository)
    ],
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
) -> CreateBracketPort:
    return CreateBracketAdapter(
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
        season_repository,
        season_modality_repository,
    )


def get_resort_bracket_port(
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    bracket_group_repository: Annotated[
        BracketGroupRepositoryPort, Depends(get_bracket_group_repository)
    ],
    bracket_group_team_repository: Annotated[
        BracketGroupTeamRepositoryPort, Depends(get_bracket_group_team_repository)
    ],
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
) -> ResortBracketPort:
    return ResortBracketAdapter(
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
    )


def get_update_match_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
) -> UpdateMatchPort:
    return UpdateMatchAdapter(match_repository, bracket_repository, team_repository)


def get_delete_match_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
) -> DeleteMatchPort:
    return DeleteMatchAdapter(match_repository)
