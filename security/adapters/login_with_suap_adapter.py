from typing import Optional

from security.services.refresh_token_service import RefreshTokenService
from core.security.login_with_suap_port import LoginWithSuapPort
from core.context import Context
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.security.oauth_provider_port import OAuthProviderPort
from domain.security.auth_token import AuthToken
from domain.exceptions.business_exception import BusinessException
from domain.user import User


def _clean_numeric_string(value) -> Optional[str]:
    if value is None:
        return None

    val_str = str(value).strip().replace(".", "").replace("-", "")

    if val_str and val_str.isdigit():
        return val_str

    return None


class LoginWithSuapAdapter(LoginWithSuapPort):
    def __init__(
        self,
        oauth_provider: OAuthProviderPort,
        refresh_token_service: RefreshTokenService,
        user_repository: UserRepositoryPort,
    ):
        self.oauth_provider = oauth_provider
        self.refresh_token_service = refresh_token_service
        self.user_repository = user_repository

    async def execute(self, context: Context) -> AuthToken:
        authorization_code = context.get_property("authorization_code", str)
        if not authorization_code:
            raise BusinessException("Código de autorização não informado")

        suap_user_data = await self.oauth_provider.authenticate_with_code(
            authorization_code
        )

        self._validate_suap_data(suap_user_data)

        user = await self._get_or_create_user(suap_user_data)

        (
            access_token,
            refresh_token_plain,
            _refresh_token_entity,
        ) = await self.refresh_token_service.create_tokens_for_user(
            user_id=user.id, matricula=str(user.matricula), email=user.email
        )

        context.put_property("refresh_token", refresh_token_plain)
        context.put_property("user", user)

        return access_token

    def _validate_suap_data(self, suap_data: User) -> None:
        if not suap_data.matricula:
            raise BusinessException("Matrícula não fornecida pelo SUAP")
        if not suap_data.email:
            raise BusinessException("Email não fornecido pelo SUAP")

        matricula_clean = _clean_numeric_string(suap_data.matricula)
        if matricula_clean is None:
            raise BusinessException(f"Matrícula inválida: {suap_data.matricula}")

    async def _get_or_create_user(self, suap_data: User) -> User:
        matricula_clean = _clean_numeric_string(suap_data.matricula)
        cpf_clean = _clean_numeric_string(suap_data.cpf)

        existing_user = await self.user_repository.find_by_matricula(matricula_clean)

        if existing_user:
            if not existing_user.active:
                raise BusinessException(
                    "Usuário desativado. Entre em contato com o suporte."
                )

            existing_user.name = suap_data.name
            existing_user.email = suap_data.email

            if cpf_clean is not None:
                existing_user.cpf = cpf_clean

            return await self.user_repository.save(existing_user)

        new_user = User(
            name=suap_data.name,
            email=suap_data.email,
            cpf=cpf_clean,
            matricula=matricula_clean,
            active=True,
        )

        return await self.user_repository.save(new_user)
