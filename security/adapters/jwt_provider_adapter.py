from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt

from core.security.jwt_provider_port import JWTProviderPort
from security.config import settings
from domain.auth_token import AuthToken
from domain.exceptions.business_exception import BusinessException


class JWTProviderAdapter(JWTProviderPort):
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_access_token_expire_minutes

    def create_access_token(
            self,
            user_id: UUID,
            matricula: str,
            email: Optional[str] = None,
            expires_delta: Optional[timedelta] = None
    ) -> AuthToken:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.expire_minutes
            )

        payload = {
            "sub": str(user_id),
            "matricula": matricula,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )

        return AuthToken(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_at=expire,
            user_id=user_id
        )

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            if payload.get("sub") is None:
                raise BusinessException("Token inválido")

            return payload

        except JWTError as e:
            raise BusinessException(f"Token inválido: {str(e)}")

    def get_user_id_from_token(self, token: str) -> UUID:
        payload = self.verify_token(token)
        return UUID(payload["sub"])

    def refresh_token(self, old_token: str) -> AuthToken:
        payload = self.verify_token(old_token)

        return self.create_access_token(
            user_id=UUID(payload["sub"]),
            matricula=payload["matricula"],
            email=payload.get("email")
        )