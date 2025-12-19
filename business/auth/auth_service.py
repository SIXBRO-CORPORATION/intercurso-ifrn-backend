from core.security.jwt_provider_port import JWTProviderPort
from core.security.oauth_provider_port import OAuthProviderPort
from domain.user import User
from domain.exceptions.business_exception import BusinessException

class AuthService:

    def __init__(
        self,
        token_provider: JWTProviderPort,
        oauth_provider: OAuthProviderPort
    ):
        self.jwt_provider = token_provider
        self.oauth_provider = oauth_provider

    async def get_authenticated_user(self, token: str) -> User:
        payload = self.jwt_provider.verify_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise BusinessException("Token sem subject")

        provider = payload.get("provider")

        if provider == "suap":
            access_token = payload.get("access_token")

            if not access_token:
                raise BusinessException("Token SUAP ausente")

            return await self.oauth_provider.get_user_info(access_token)

        raise BusinessException("Provedor de autenticação desconhecido")
