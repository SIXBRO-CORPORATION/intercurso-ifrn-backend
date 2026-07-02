from typing import Annotated
from fastapi import Depends

from core.business.team.create_team_port import CreateTeamPort
from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from business.team.create_team_adapter import CreateTeamAdapter
from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from web.dependencies.persistence_dependencies import (
    get_user_repository,
    get_team_repository,
    get_team_member_repository,
    get_season_repository,
    get_season_modality_repository,
    get_modality_repository,
)


def get_create_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
) -> CreateTeamPort:
    return CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
    )


def get_approve_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
) -> ApproveTeamPort:
    return ApproveTeamAdapter(team_repository, team_member_repository)


def get_confirm_donation_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> ConfirmDonationPort:
    return ConfirmDonationAdapter(
        team_repository, team_member_repository, user_repository
    )
