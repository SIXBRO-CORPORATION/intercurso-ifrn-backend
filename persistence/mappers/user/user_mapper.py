from typing import Optional

from domain.enums.gender import Gender
from domain.enums.user_role import UserRole
from domain.user.user import User
from persistence.model.user.user_entity import UserEntity


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
            role=UserRole[entity.role] if entity.role else UserRole.USER,
            gender=Gender(entity.gender) if entity.gender else None,
            tipo_usuario=entity.tipo_usuario,
            campus=entity.campus,
            curso=entity.curso,
            turno=entity.turno,
            email_classroom=entity.email_classroom,
            photo=entity.photo,
            birth_date=entity.birth_date,
            frequencia_percentual=entity.frequencia_percentual,
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
            role=(user.role or UserRole.USER).name,
            gender=user.gender.value if user.gender else None,
            tipo_usuario=user.tipo_usuario,
            campus=user.campus,
            curso=user.curso,
            turno=user.turno,
            email_classroom=user.email_classroom,
            photo=user.photo,
            birth_date=user.birth_date,
            frequencia_percentual=user.frequencia_percentual,
        )

        return entity
