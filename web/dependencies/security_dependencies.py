from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.adapters.refresh_token_adapter import RefreshTokenRepositoryAdapter
from persistence.mappers.refresh_token_mapper import RefreshTokenMapper
from persistence.database import get_db
from business.auth.refresh_token_service import RefreshTokenService
from core.security.jwt_provider_port import JWTProviderPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.security.oauth_provider_port import OAuthProviderPort
from core.persistence.refresh_token_repository_port import RefreshTokenRepositoryPort
from domain.user import User
from security.adapters.jwt_provider_adapter import JWTProviderAdapter
from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter
from security.utils import (
    validate_user_active,
    extract_token_from_credentials,
    verify_and_extract_user_id,
    security_scheme,
)
from web.dependencies.persistence_dependencies import get_user_repository



def get_jwt_provider() -> JWTProviderPort:
    return JWTProviderAdapter()

def get_refresh_token_repository(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> RefreshTokenRepositoryPort:
    mapper = RefreshTokenMapper()
    return RefreshTokenRepositoryAdapter(session, mapper)

def get_refresh_token_service(
        jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
        refresh_token_repository: RefreshTokenRepositoryPort = Depends(get_refresh_token_repository),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
) -> RefreshTokenService:
    return RefreshTokenService(
        jwt_provider=jwt_provider,
        refresh_token_repository=refresh_token_repository,
        user_repository=user_repository
    )

def get_oauth_provider() -> OAuthProviderPort:
    return SUAPOAuthAdapter()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
) -> UUID:
    token = extract_token_from_credentials(credentials)
    user_id = verify_and_extract_user_id(token, jwt_provider)

    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
) -> User:
    user = await user_repository.get(user_id)

    validate_user_active(user)

    return user


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

    except Exception:
        return None


def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
