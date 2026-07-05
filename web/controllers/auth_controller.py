from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from core.security.login_with_suap_port import LoginWithSuapPort
from core.security.logout_port import LogoutPort
from core.security.refresh_access_token_port import RefreshAccessTokenPort
from core.context import Context
from core.security.oauth_provider_port import OAuthProviderPort
from domain.exceptions.business_exception import BusinessException
from domain.user import User
from security.config import settings
from security.utils.oauth_state import (
    OAUTH_STATE_COOKIE_NAME,
    generate_oauth_state,
    is_valid_oauth_state,
)
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_login_with_suap_port,
    get_logout_port,
    get_oauth_provider,
    get_optional_current_user,
    get_refresh_access_token_port,
    get_user_model_mapper,
)
from web.mappers.user_model_mapper import UserModelMapper
from web.models.response.user_response import UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
_REFRESH_TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 dias, igual ao RefreshTokenService
_OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60  # 10 minutos


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=_REFRESH_TOKEN_MAX_AGE_SECONDS,
        path="/api/auth",
    )


@router.get("/login/suap")
async def login_with_suap(
    oauth_provider: OAuthProviderPort = Depends(get_oauth_provider),
):
    state = generate_oauth_state()
    authorization_url = oauth_provider.get_authorization_url(state=state)

    response = RedirectResponse(url=authorization_url)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=_OAUTH_STATE_MAX_AGE_SECONDS,
        path="/api/auth",
    )

    return response


@router.get("/callback")
async def auth_callback(
    code: str = Query(..., description="Authorization code from SUAP"),
    state: str = Query(..., description="State retornado pelo SUAP"),
    oauth_state_cookie: Optional[str] = Cookie(None, alias=OAUTH_STATE_COOKIE_NAME),
    login_with_suap_port: LoginWithSuapPort = Depends(get_login_with_suap_port),
):
    if not is_valid_oauth_state(state, oauth_state_cookie):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado. Tente fazer login novamente.",
        )

    context = Context()
    context.put_property("authorization_code", code)

    try:
        access_token = await login_with_suap_port.execute(context)
    except BusinessException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    refresh_token = context.get_property("refresh_token", str)

    frontend_url = settings.frontend_url
    redirect_url = f"{frontend_url}/auth/callback?token={access_token.access_token}"

    response = RedirectResponse(url=redirect_url)
    response.delete_cookie(OAUTH_STATE_COOKIE_NAME, path="/api/auth")

    if refresh_token:
        _set_refresh_token_cookie(response, refresh_token)

    return response


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    user: User = Depends(get_optional_current_user),
    mapper: UserModelMapper = Depends(get_user_model_mapper),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado"
        )

    user_response = mapper.to_response(user)

    return ApiResponse.success(
        data=user_response, message="User retrieved successfully"
    )


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    refresh_access_token_port: RefreshAccessTokenPort = Depends(
        get_refresh_access_token_port
    ),
):
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente",
        )

    context = Context()
    context.put_property("refresh_token", refresh_token_cookie)

    try:
        new_access_token = await refresh_access_token_port.execute(context)
    except BusinessException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    new_refresh_token = context.get_property("new_refresh_token", str)
    if new_refresh_token:
        _set_refresh_token_cookie(response, new_refresh_token)

    return ApiResponse.success(
        data={
            "access_token": new_access_token.access_token,
            "token_type": new_access_token.token_type,
            "expires_at": new_access_token.expires_at,
        },
        message="Token refreshed successfully",
    )


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    user: Optional[User] = Depends(get_optional_current_user),
    logout_port: LogoutPort = Depends(get_logout_port),
):
    context = Context()

    if refresh_token_cookie:
        context.put_property("refresh_token", refresh_token_cookie)
    elif user:
        context.put_property("user_id", user.id)

    await logout_port.execute(context)

    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path="/api/auth")

    return ApiResponse.success(message="Logged out successfully")
