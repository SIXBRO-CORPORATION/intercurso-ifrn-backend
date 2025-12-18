from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security.jwt_provider_port import JWTProviderPort
from domain.exceptions.business_exception import BusinessException

security_scheme = HTTPBearer()


def extract_token_from_credentials(
        credentials: Optional[HTTPAuthorizationCredentials]
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def verify_and_extract_user_id(
        token: str,
        jwt_provider: JWTProviderPort
) -> UUID:
    try:
        user_id = jwt_provider.get_user_id_from_token(token)
        return user_id

    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_user_active(user) -> None:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Entre em contato com o suporte."
        )