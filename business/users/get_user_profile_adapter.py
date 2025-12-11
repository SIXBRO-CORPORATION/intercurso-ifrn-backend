from uuid import UUID

from core.business.users.get_user_profile_port import GetUserProfilePort
from core.context import Context
from core.persistence.user_repository_port import UserRepositoryPort
from domain.user import User


class GetUserProfileAdapter(GetUserProfilePort):
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository

    async def execute(self, context: Context) -> User:
        userId = context.get_property("userId", UUID)

        if userId is None:
            raise RuntimeError("User ID is required")

        user = self.repository.get(userId)
        if user is None:
            raise RuntimeError("User not found")

        return user