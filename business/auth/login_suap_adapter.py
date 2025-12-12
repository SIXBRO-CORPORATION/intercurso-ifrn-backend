from core.business.auth.oauth_provider_port import OAuthProviderPort
from core.business.auth.jwt_provider_port import TokenServicePort
from core.context import Context
from core.persistence.user_repository_port import UserRepositoryPort
from domain.auth_token import AuthToken
from domain.user import User

class LoginWithSUAPAdapter:

    def __init__(self, oauth_provider: OAuthProviderPort, token_service: TokenServicePort, user_repository: UserRepositoryPort ):
        self.oauth_provider = oauth_provider
        self.token_service = token_service
        self.user_repository = user_repository

    async def execute(self, authorization_code: str) -> AuthToken:
        suap_user_data = await self.suap_service.authenticate_with_code(
            authorization_code
        )

        user = await self._get_or_create_user(suap_user_data)

        token = self.jwt_service.create_access_token(
            user_id=user.id,
            matricula=str(user.matricula),
            email=user.email
        )

        return token

    async def _get_or_create_user(self, suap_data) -> User:
        existing_user = await self.user_repository.find_by_matricula(
            int(suap_data.matricula)
        )

        if existing_user:
            existing_user.name = suap_data.nome_usual
            existing_user.email = suap_data.email
            existing_user.active = True

            return await self.user_repository.save(existing_user)

        else:
            new_user = User(
                name=suap_data.nome_usual,
                email=suap_data.email,
                cpf=int(suap_data.cpf) if suap_data.cpf else None,
                matricula=int(suap_data.matricula),
                active=True
            )

            return await self.user_repository.save(new_user)