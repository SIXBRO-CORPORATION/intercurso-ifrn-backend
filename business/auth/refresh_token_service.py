from datetime import datetime, timedelta
from typing import Tuple
from uuid import UUID

from core.persistence.refresh_token_repository_port import RefreshTokenRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.security.jwt_provider_port import JWTProviderPort
from domain.auth_token import AuthToken
from domain.exceptions.business_exception import BusinessException
from domain.refresh_token import RefreshToken


class RefreshTokenService:
    def __init__(
            self,
            jwt_provider: JWTProviderPort,
            refresh_token_repository: RefreshTokenRepositoryPort,
            user_repository: UserRepositoryPort
    ):
        self.jwt_provider = jwt_provider
        self.refresh_token_repository = refresh_token_repository
        self.user_repository = user_repository
        self.refresh_token_expire_days = 30

    async def create_tokens_for_user(
            self,
            user_id: UUID,
            matricula: str,
            email: str
    ) -> Tuple[AuthToken, str, RefreshToken]:
        access_token, refresh_token_plain = self.jwt_provider.create_token_pair(
            user_id=user_id,
            matricula=matricula,
            email=email
        )

        token_hash = self.jwt_provider.hash_token(refresh_token_plain)

        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        refresh_token_entity = RefreshToken(
            user_id=user_id,
            token=token_hash,
            expires_at=expires_at,
            revoked=False
        )

        await self.refresh_token_repository.save(refresh_token_entity)

        return access_token, refresh_token_plain, refresh_token_entity

    async def refresh_access_token(
            self,
            refresh_token: str
    ) -> Tuple[AuthToken, str, RefreshToken]:
        token_hash = self.jwt_provider.hash_token(refresh_token)

        stored_token = await self.refresh_token_repository.find_by_token(token_hash)
        if not stored_token:
            raise BusinessException("Refresh token inválido")

        stored_token.validate()

        user = await self.user_repository.get(stored_token.user_id)
        if not user:
            raise BusinessException("Usuário não encontrado")

        if not user.active:
            raise BusinessException("Usuário inativo")

        new_access_token, new_refresh_token_plain, new_token_entity = (
            await self.create_tokens_for_user(
                user_id=user.id,
                matricula=str(user.matricula),
                email=user.email
            )
        )

        stored_token.rotate(new_token_entity.id)
        await self.refresh_token_repository.save(stored_token)

        return new_access_token, new_refresh_token_plain, new_token_entity

    async def revoke_token(self, refresh_token: str) -> None:
        token_hash = self.jwt_provider.hash_token(refresh_token)
        stored_token = await self.refresh_token_repository.find_by_token(token_hash)

        if not stored_token:
            raise BusinessException("Token não encontrado")

        stored_token.revoke()
        await self.refresh_token_repository.save(stored_token)

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        return await self.refresh_token_repository.revoke_all_by_user(user_id)
