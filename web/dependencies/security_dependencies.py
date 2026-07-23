from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from core.security.jwt_provider_port import JWTProviderPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.user_role import UserRole
from domain.user.user import User
from security.adapters.jwt_provider_adapter import JWTProviderAdapter
from security.utils import (
    validate_user_active,
    extract_token_from_credentials,
    verify_and_extract_user_id,
    security_scheme,
    optional_security_scheme,
)
from web.dependencies.persistence_dependencies import get_user_repository


def get_jwt_provider() -> JWTProviderPort:
    return JWTProviderAdapter()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
) -> UUID:
    token = extract_token_from_credentials(credentials)
    user_id = verify_and_extract_user_id(token, jwt_provider)

    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
) -> User:
    user = await user_repository.get(user_id)

    validate_user_active(user)

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        optional_security_scheme
    ),
    jwt_provider: JWTProviderPort = Depends(get_jwt_provider),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token = extract_token_from_credentials(credentials)
        user_id = verify_and_extract_user_id(token, jwt_provider)
        user = await user_repository.get(user_id)

        return user if user and user.active else None

    except Exception:
        return None


def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_role(*allowed_roles: UserRole):

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.ADMIN:
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para realizar essa ação",
            )

        return current_user

    return _dependency


def require_monitor(
    current_user: User = Depends(require_role(UserRole.MONITOR)),
) -> User:
    return current_user


def require_admin(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> User:
    return current_user
