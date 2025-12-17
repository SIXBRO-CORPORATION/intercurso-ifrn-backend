from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.jwt_provider_port import TokenServicePort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.user import User
from security.adapters.jwt_token_adapter import JWTTokenAdapter
from persistence.adapters.user_repository_adapter import UserRepositoryAdapter
from persistence.database import get_db
from persistence.mappers.user_mapper import UserMapper

security = HTTPBearer()


def get_token_service() -> TokenServicePort:
    return JWTTokenAdapter()


def get_user_repository(
        db: AsyncSession = Depends(get_db)
) -> UserRepositoryPort:
    return UserRepositoryAdapter(db, UserMapper())


async def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        token_service: TokenServicePort = Depends(get_token_service)
) -> UUID:
    try:
        token = credentials.credentials
        user_id = token_service.get_user_id_from_token(token)
        return user_id

    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        user_id: UUID = Depends(get_current_user_id),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
) -> User:
    user = await user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_optional_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
        user_repository: UserRepositoryPort = Depends(get_user_repository)
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token_service = get_token_service()
        user_id = token_service.get_user_id_from_token(credentials.credentials)

        user = await user_repository.get(user_id)
        return user if user and user.active else None

    except:
        return None