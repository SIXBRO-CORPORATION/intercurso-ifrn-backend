from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from business.team.create_team_adapter import CreateTeamAdapter
from business.team.create_team_members_adapter import CreateTeamMembersAdapter
from business.users.create_user_adapter import CreateUserAdapter
from business.users.get_user_profile_adapter import GetUserProfileAdapter
from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.create_team_members_port import CreateTeamMembersPort
from core.business.team.create_team_port import CreateTeamPort
from core.business.users.create_user_port import CreateUserPort
from core.business.users.get_user_profile_port import GetUserProfilePort
from persistence.adapters.team_member_repository_adapter import TeamMemberRepositoryAdapter
from persistence.adapters.team_repository_adapter import TeamRepositoryAdapter
from persistence.adapters.user_repository_adapter import UserRepositoryAdapter
from persistence.database import get_db
from persistence.mappers.team_mapper import TeamMapper
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper

def get_team_repository(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> TeamRepositoryAdapter:
    mapper = TeamMapper()
    return TeamRepositoryAdapter(session, mapper)


def get_team_member_repository(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> TeamMemberRepositoryAdapter:
    team_member_mapper = TeamMemberMapper()
    user_mapper = UserMapper()
    return TeamMemberRepositoryAdapter(session, team_member_mapper, user_mapper)


def get_user_repository(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> UserRepositoryAdapter:
    mapper = UserMapper()
    return UserRepositoryAdapter(session, mapper)


def get_create_user_port(
        user_repository: Annotated[UserRepositoryAdapter, Depends(get_user_repository)]
) -> CreateUserPort:
    return CreateUserAdapter(user_repository)


def get_user_profile_port(
        user_repository: Annotated[UserRepositoryAdapter, Depends(get_user_repository)]
) -> GetUserProfilePort:
    return GetUserProfileAdapter(user_repository)


def get_create_team_members_port(
        team_member_repository: Annotated[TeamMemberRepositoryAdapter, Depends(get_team_member_repository)],
        user_repository: Annotated[UserRepositoryAdapter, Depends(get_user_repository)]
) -> CreateTeamMembersPort:
    return CreateTeamMembersAdapter(team_member_repository, user_repository)


def get_create_team_port(
        team_repository: Annotated[TeamRepositoryAdapter, Depends(get_team_repository)],
        team_member_repository: Annotated[TeamMemberRepositoryAdapter, Depends(get_team_member_repository)],
        user_repository: Annotated[UserRepositoryAdapter, Depends(get_user_repository)],
        create_team_members_port: Annotated[CreateTeamMembersPort, Depends(get_create_team_members_port)]
) -> CreateTeamPort:
    return CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        create_team_members_port
    )


def get_approve_team_port(
        team_repository: Annotated[TeamRepositoryAdapter, Depends(get_team_repository)]
) -> ApproveTeamPort:
    return ApproveTeamAdapter(team_repository)


def get_confirm_donation_port(
        team_repository: Annotated[TeamRepositoryAdapter, Depends(get_team_repository)],
        team_member_repository: Annotated[TeamMemberRepositoryAdapter, Depends(get_team_member_repository)],
        user_repository: Annotated[UserRepositoryAdapter, Depends(get_user_repository)]
) -> ConfirmDonationPort:
    return ConfirmDonationAdapter(
        team_repository,
        team_member_repository,
        user_repository
    )