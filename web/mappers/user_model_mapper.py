from typing import Optional

from domain.user import User
from web.models.response.user_response import UserResponse


class UserModelMapper:
    def to_response(self, user: Optional[User]) -> Optional[UserResponse]:
        if User is None:
            return None

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            matricula=user.matricula,
            cpf=user.cpf,
            created_at=user.created_at,
            modified_at=user.modified_at,
            active=user.active
        )