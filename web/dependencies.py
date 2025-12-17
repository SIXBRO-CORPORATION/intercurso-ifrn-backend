from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.jwt_provider_port import JWTProviderPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.user import User
from security.adapters.jwt_provider_adapter import JWTProviderAdapter
from persistence.database import get_db

security = HTTPBearer()


def get_jwt_provider_port() -> JWTProviderPort:
    return JWTProviderAdapter()


def get_user_repository(
        db: AsyncSession = Depends(get_db)
) -> UserRepositoryPort:
    return UserRepositoryAdapter(db, UserMapper())


async def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        token_service: JWTProviderPort = Depends(get_jwt_provider_port)
) -> UUID:
    try:
        token = credentials.credentials
        user_id = token_service.get_user_id_from_token(token)
        return user_id

    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        user_id: UUID = Depends(get_current_user_id),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
) -> User:
    user = await user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_optional_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token_service = get_jwt_provider_port()
        user_id = token_service.get_user_id_from_token(credentials.credentials)

        user = await user_repository.get(user_id)
        return user if user and user.active else None

    except:
        return None
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
