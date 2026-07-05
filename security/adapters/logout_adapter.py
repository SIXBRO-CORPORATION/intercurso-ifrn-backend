from uuid import UUID

from security.services.refresh_token_service import RefreshTokenService
from core.security.logout_port import LogoutPort
from core.context import Context
from domain.exceptions.business_exception import BusinessException


class LogoutAdapter(LogoutPort):
    def __init__(self, refresh_token_service: RefreshTokenService):
        self.refresh_token_service = refresh_token_service

    async def execute(self, context: Context) -> None:
        refresh_token = context.get_property("refresh_token", str)

        if refresh_token:
            try:
                await self.refresh_token_service.revoke_token(refresh_token)
            except BusinessException:
                pass
            return

        user_id = context.get_property("user_id", UUID)
        if user_id:
            await self.refresh_token_service.revoke_all_user_tokens(user_id)
