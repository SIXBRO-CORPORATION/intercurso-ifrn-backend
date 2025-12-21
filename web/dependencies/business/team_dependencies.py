from typing import Annotated
from fastapi import Depends

from core.business.team.create_team_port import CreateTeamPort
from core.business.team.create_team_members_port import CreateTeamMembersPort
from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from business.team.create_team_adapter import CreateTeamAdapter
from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.create_team_members_adapter import CreateTeamMembersAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from web.dependencies.persistence_dependencies import (
    get_user_repository,
    get_team_repository,
    get_team_member_repository,
)


def get_create_team_members_port(
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> CreateTeamMembersPort:
    return CreateTeamMembersAdapter(team_member_repository, user_repository)


def get_create_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    create_team_members_port: Annotated[
        CreateTeamMembersPort, Depends(get_create_team_members_port)
    ],
) -> CreateTeamPort:
    return CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        create_team_members_port,
    )


def get_approve_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
) -> ApproveTeamPort:
    return ApproveTeamAdapter(team_repository)


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
