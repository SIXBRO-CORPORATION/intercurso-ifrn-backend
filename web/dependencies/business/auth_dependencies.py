from typing import Annotated

from fastapi import Depends

from security.adapters.login_with_suap_adapter import LoginWithSuapAdapter
from security.adapters.logout_adapter import LogoutAdapter
from security.adapters.refresh_access_token_adapter import RefreshAccessTokenAdapter
from security.services.refresh_token_service import RefreshTokenService
from core.security.login_with_suap_port import LoginWithSuapPort
from core.security.logout_port import LogoutPort
from core.security.refresh_access_token_port import RefreshAccessTokenPort
from core.persistence.security.refresh_token_repository_port import RefreshTokenRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.security.jwt_provider_port import JWTProviderPort
from core.security.oauth_provider_port import OAuthProviderPort
from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter
from web.dependencies.persistence_dependencies import (
    get_refresh_token_repository,
    get_user_repository,
)
from web.dependencies.security_dependencies import get_jwt_provider


def get_oauth_provider() -> OAuthProviderPort:
    return SUAPOAuthAdapter()


def get_refresh_token_service(
    jwt_provider: Annotated[JWTProviderPort, Depends(get_jwt_provider)],
    refresh_token_repository: Annotated[
        RefreshTokenRepositoryPort, Depends(get_refresh_token_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> RefreshTokenService:
    return RefreshTokenService(
        jwt_provider=jwt_provider,
        refresh_token_repository=refresh_token_repository,
        user_repository=user_repository,
    )


def get_login_with_suap_port(
    oauth_provider: Annotated[OAuthProviderPort, Depends(get_oauth_provider)],
    refresh_token_service: Annotated[
        RefreshTokenService, Depends(get_refresh_token_service)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> LoginWithSuapPort:
    return LoginWithSuapAdapter(
        oauth_provider=oauth_provider,
        refresh_token_service=refresh_token_service,
        user_repository=user_repository,
    )


def get_refresh_access_token_port(
    refresh_token_service: Annotated[
        RefreshTokenService, Depends(get_refresh_token_service)
    ],
) -> RefreshAccessTokenPort:
    return RefreshAccessTokenAdapter(refresh_token_service=refresh_token_service)


def get_logout_port(
    refresh_token_service: Annotated[
        RefreshTokenService, Depends(get_refresh_token_service)
    ],
) -> LogoutPort:
    return LogoutAdapter(refresh_token_service=refresh_token_service)
