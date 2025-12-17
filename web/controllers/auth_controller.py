from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from security.adapters.login_suap_adapter import LoginWithSUAPAdapter
from core.security.oauth_provider_port import OAuthProviderPort
from core.security.jwt_provider_port import TokenServicePort
from security.config import settings
from core.persistence.user_repository_port import UserRepositoryPort
from domain.user import User
from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter
from web.commons.ApiResponse import ApiResponse
from web.dependencies.auth import (
    get_current_user,
    get_token_service,
    get_user_repository
)
from web.models.response.user_response import UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_oauth_provider() -> OAuthProviderPort:
    return SUAPOAuthAdapter()


@router.get("/login/suap")
async def login_with_suap(
        oauth_provider: OAuthProviderPort = Depends(get_oauth_provider)
):
    authorization_url = oauth_provider.get_authorization_url()
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def auth_callback(
        code: str = Query(..., description="Authorization code from SUAP"),
        oauth_provider: OAuthProviderPort = Depends(get_oauth_provider),
        token_service: TokenServicePort = Depends(get_token_service),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    # Instancia o caso de uso com as dependências injetadas
    login_use_case = LoginWithSUAPAdapter(
        oauth_provider=oauth_provider,
        token_service=token_service,
        user_repository=user_repository
    )

    # Executa o caso de uso
    token = await login_use_case.execute(code)

    # Redireciona para frontend
    frontend_url = settings.frontend_url
    redirect_url = f"{frontend_url}/auth/callback?token={token.access_token}"

    return RedirectResponse(url=redirect_url)


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse]
)
async def get_current_user_info(
        user: User = Depends(get_current_user)
):
    from web.mappers.user_model_mapper import UserModelMapper

    mapper = UserModelMapper()
    user_response = mapper.to_response(user)

    return ApiResponse.success(
        data=user_response,
        message="User retrieved successfully"
    )


@router.post("/refresh")
async def refresh_token(
        user: User = Depends(get_current_user),
        token_service: TokenServicePort = Depends(get_token_service)
):
    new_token = token_service.create_access_token(
        user_id=user.id,
        matricula=str(user.matricula),
        email=user.email
    )

    return ApiResponse.success(
        data={
            "access_token": new_token.access_token,
            "token_type": new_token.token_type,
            "expires_at": new_token.expires_at
        },
        message="Token refreshed successfully"
    )


@router.post("/logout")
async def logout():
    return ApiResponse.success(
        message="Logged out successfully"
    )