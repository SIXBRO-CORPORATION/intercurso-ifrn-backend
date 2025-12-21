from typing import Optional

from domain.user import User
from persistence.model.user_entity import UserEntity


class UserMapper:
    def to_domain(self, entity: Optional[UserEntity]) -> Optional[User]:
        if entity is None:
            return None

        return User(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            cpf=entity.cpf,
            matricula=entity.matricula,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active,
            atleta=entity.atleta,
        )

    def to_entity(self, user: User) -> UserEntity:
        entity = UserEntity(
            id=user.id,
            name=user.name,
            email=user.email,
            cpf=user.cpf,
            matricula=user.matricula,
            created_at=user.created_at,
            modified_at=user.modified_at,
            active=user.active,
            atleta=user.atleta,
        )

        return entity
