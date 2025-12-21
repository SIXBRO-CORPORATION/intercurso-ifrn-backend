from typing import Annotated
from fastapi import Depends

from core.business.users.create_user_port import CreateUserPort
from core.business.users.get_user_profile_port import GetUserProfilePort
from core.persistence.user_repository_port import UserRepositoryPort
from business.users.create_user_adapter import CreateUserAdapter
from business.users.get_user_profile_adapter import GetUserProfileAdapter
from web.dependencies.persistence_dependencies import get_user_repository


def create_user_port(
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> CreateUserPort:
    return CreateUserAdapter(user_repository)


def get_user_profile_port(
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> GetUserProfilePort:
    return GetUserProfileAdapter(user_repository)
