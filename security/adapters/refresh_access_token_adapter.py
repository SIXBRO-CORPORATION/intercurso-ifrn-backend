from security.services.refresh_token_service import RefreshTokenService
from core.security.refresh_access_token_port import RefreshAccessTokenPort
from core.context import Context
from domain.auth_token import AuthToken
from domain.exceptions.business_exception import BusinessException


class RefreshAccessTokenAdapter(RefreshAccessTokenPort):
    def __init__(self, refresh_token_service: RefreshTokenService):
        self.refresh_token_service = refresh_token_service

    async def execute(self, context: Context) -> AuthToken:
        refresh_token = context.get_property("refresh_token", str)
        if not refresh_token:
            raise BusinessException("Refresh token não informado")

        (
            new_access_token,
            new_refresh_token_plain,
            _new_refresh_token_entity,
        ) = await self.refresh_token_service.refresh_access_token(refresh_token)

        context.put_property("new_refresh_token", new_refresh_token_plain)

        return new_access_token
