from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from jose import JWTError, jwt, ExpiredSignatureError

from jwt.exceptions import (
    InvalidTokenError,
    InvalidSignatureError,
    DecodeError,
)

from core.security.jwt_provider_port import JWTProviderPort
from domain.exceptions.jwt_exception import (
    JWTExpiredError,
    JWTValidationError,
    JWTDecodeError,
)
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
        expires_delta: Optional[timedelta] = None,
    ) -> AuthToken:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)

        payload = {
            "sub": str(user_id),
            "matricula": matricula,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return AuthToken(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_at=expire,
            user_id=user_id,
        )

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "require": ["sub", "exp", "iat"],
                },
            )

            return payload

        except ExpiredSignatureError:
            raise JWTExpiredError("Token Expirado")

        except InvalidSignatureError:
            raise JWTValidationError("Assinatura do token inválida")

        except DecodeError as e:
            raise JWTDecodeError(f"Token malformado: {str(e)}")

        except InvalidTokenError as e:
            raise JWTDecodeError(f"Token inválido: {str(e)}")

        except Exception as e:
            raise JWTDecodeError(f"Erro ao decodificar token: {str(e)}")

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("sub") is None:
                raise BusinessException("Token inválido")

            return payload

        except JWTError as e:
            raise BusinessException(f"Token inválido: {str(e)}")

    def get_user_id_from_token(self, token: str) -> UUID:
        payload = self.verify_token(token)
        return UUID(payload["sub"])

    def refresh_token(self, old_token: str) -> AuthToken:
        try:
            payload = jwt.decode(
                old_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )

            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_date = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                max_refresh_date = datetime.now(timezone.utc) - timedelta(days=7)

                if exp_date < max_refresh_date:
                    raise JWTExpiredError("Token muito antigo para ser renovado")

            user_id = payload.get("sub")
            if not user_id:
                raise JWTDecodeError("Token não contém ID do usuário")

            excluded_claims = {"sub", "exp", "iat", "type"}
            additional_claims = {
                k: v for k, v in payload.items() if k not in excluded_claims
            }

            return self.generate_token(
                user_id=user_id,
                additional_claims=additional_claims if additional_claims else None,
            )

        except (JWTDecodeError, JWTExpiredError):
            raise

        except Exception as e:
            raise JWTDecodeError(f"Erro ao renovar token: {str(e)}")
