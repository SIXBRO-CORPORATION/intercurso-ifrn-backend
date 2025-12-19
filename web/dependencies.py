from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

# ============ IMPORTS - CORE ============
from core.security.jwt_provider_port import JWTProviderPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort

from core.business.users.create_user_port import CreateUserPort
from core.business.users.get_user_profile_port import GetUserProfilePort
from core.business.team.create_team_port import CreateTeamPort
from core.business.team.create_team_members_port import CreateTeamMembersPort
from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.security.oauth_provider_port import OAuthProviderPort

# ============ IMPORTS - DOMAIN ============
from domain.user import User
from domain.exceptions.business_exception import BusinessException

# ============ IMPORTS - SECURITY ============
from security.adapters.jwt_provider_adapter import JWTProviderAdapter
from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter
from security.utils import (
    extract_token_from_credentials,
    verify_and_extract_user_id,
    validate_user_active,
    security_scheme,
)

# ============ IMPORTS - PERSISTENCE ============
from persistence.database import get_db
from persistence.mappers.user_mapper import UserMapper
from persistence.mappers.team_mapper import TeamMapper
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.adapters.user_repository_adapter import UserRepositoryAdapter
from persistence.adapters.team_repository_adapter import TeamRepositoryAdapter
from persistence.adapters.team_member_repository_adapter import (
    TeamMemberRepositoryAdapter,
)

# ============ IMPORTS - BUSINESS ============
from business.users.create_user_adapter import CreateUserAdapter
from business.users.get_user_profile_adapter import GetUserProfileAdapter
from business.team.create_team_adapter import CreateTeamAdapter
from business.team.create_team_members_adapter import CreateTeamMembersAdapter
from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from business.auth.auth_service import AuthService

# ============================================================================
# PERSISTENCE - Repositórios
# ============================================================================


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepositoryPort:
    mapper = UserMapper()
    return UserRepositoryAdapter(session, mapper)

def get_team_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TeamRepositoryPort:
    mapper = TeamMapper()
    return TeamRepositoryAdapter(session, mapper)


def get_team_member_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TeamMemberRepositoryPort:
    team_member_mapper = TeamMemberMapper()
    user_mapper = UserMapper()
    return TeamMemberRepositoryAdapter(session, team_member_mapper, user_mapper)


# ============================================================================
# SECURITY - Autenticação e Autorização
# ============================================================================


def get_jwt_provider() -> JWTProviderPort:
    return JWTProviderAdapter()


def get_auth_service() -> AuthService:
    return AuthService(
        token_provider=JWTProviderAdapter(),
        oauth_provider=SUAPOAuthAdapter(),
    )

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
) -> UUID:
    token = extract_token_from_credentials(credentials)

    user_id = verify_and_extract_user_id(token, jwt_provider)

    return user_id


async def get_current_user(
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
) -> User:
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(401, "Authorization header ausente")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Formato inválido")

    token = auth_header.replace("Bearer ", "")

    try:
        return await auth_service.get_authenticated_user(token)
    except BusinessException as e:
        raise HTTPException(status_code=401, detail=str(e))

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        lambda: security_scheme(auto_error=False)
    ),
    jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token = extract_token_from_credentials(credentials)

        user_id = verify_and_extract_user_id(token, jwt_provider)

        user = await user_repository.get(user_id)

        return user if user and user.active else None

    except:
        return None


def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


# ============================================================================
# BUSINESS - Casos de Uso
# ============================================================================


def get_create_user_port(
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> CreateUserPort:
    return CreateUserAdapter(user_repository)


def get_user_profile_port(
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> GetUserProfilePort:
    return GetUserProfileAdapter(user_repository)


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
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
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


def get_confirm_donation_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> ConfirmDonationPort:
    return ConfirmDonationAdapter(
        team_repository, team_member_repository, user_repository
    )
