from core.security.oauth_provider_port import OAuthProviderPort
from core.security.jwt_provider_port import TokenServicePort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.auth_token import AuthToken
from domain.user import User
from typing import Optional
from domain.exceptions.business_exception import BusinessException


def _safe_int_conversion(value) -> Optional[int]:
    if value is None:
        return None

    val_str = str(value).strip().replace(".", "").replace("-", "")

    if val_str and val_str.isdigit():
        return int(val_str)

    return None

class LoginWithSUAPAdapter:

    def __init__(self, oauth_provider: OAuthProviderPort, token_service: TokenServicePort, user_repository: UserRepositoryPort ):
        self.oauth_provider = oauth_provider
        self.token_service = token_service
        self.user_repository = user_repository


    async def execute(self, authorization_code: str) -> AuthToken:
        suap_user_data = await self.oauth_provider.authenticate_with_code(
            authorization_code
        )

        self._validate_suap_data(suap_user_data)

        user = await self._get_or_create_user(suap_user_data)

        token = self.token_service.create_access_token(
            user_id=user.id,
            matricula=str(user.matricula),
            email=user.email
        )

        return token

    def _validate_suap_data(self, suap_data) -> None:
        if not suap_data.matricula:
            raise BusinessException("Matrícula não fornecida pelo SUAP")
        if not suap_data.email:
            raise BusinessException("Email não fornecido pelo SUAP")

        matricula_int = _safe_int_conversion(suap_data.matricula)
        if matricula_int is None:
            raise BusinessException(f"Matrícula inválida: {suap_data.matricula}")

    async def _get_or_create_user(self, suap_data) -> User:
        matricula_int = _safe_int_conversion(suap_data.matricula)
        cpf_int = _safe_int_conversion(suap_data.cpf)

        # Busca usuário existente
        existing_user = await self.user_repository.find_by_matricula(matricula_int)

        if existing_user:
            # Atualiza dados do usuário existente
            existing_user.name = suap_data.nome_usual
            existing_user.email = suap_data.email
            existing_user.active = True

            # Atualiza CPF apenas se veio válido do SUAP
            if cpf_int is not None:
                existing_user.cpf = cpf_int

            return await self.user_repository.save(existing_user)

        else:
            new_user = User(
                name=suap_data.nome_usual,
                email=suap_data.email,
                cpf=cpf_int,
                matricula=matricula_int,
                active=True
            )

            return await self.user_repository.save(new_user)