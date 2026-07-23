from typing import Optional

from domain.user.user import User
from web.models.response.user_response import UserResponse


class UserModelMapper:
    def to_response(self, user: Optional[User]) -> Optional[UserResponse]:
        if user is None:
            return None

        return UserResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            matricula=user.matricula,
            role=user.role.name if user.role else None,
            atleta=bool(user.atleta),
            active=bool(user.active),
        )
