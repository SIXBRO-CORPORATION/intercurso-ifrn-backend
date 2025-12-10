from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from core.persistence.user_repository_port import UserRepositoryPort
from domain.user import User
from persistence.mappers.user_mapper import UserMapper
from persistence.model.user_entity import UserEntity


class UserRepositoryAdapter(UserRepositoryPort):
    def __init__(self, session: Session, mapper: UserMapper):
        self.session = session
        self.mapper = mapper

    def get(self, user_id: UUID) -> Optional[User]:
        entity = self.session.query(UserEntity).filter(
            UserEntity.id == user_id
        ).first()
        return self.mapper.to_domain(entity) if entity else None

    def save(self, user: User) -> User:
        entity = self.mapper.to_entity(user)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    def find_by_email(self, email: str) -> Optional[User]:
        entity = self.session.query(UserEntity).filter(
            UserEntity.email == email
        ).first()
        return self.mapper.to_domain(entity) if entity else None

    def exists_by_email(self, email: str) -> bool:
        return self.session.query(UserEntity).filter(
            UserEntity.email == email
        ).count() > 0

    def exists_by_matricula(self, matricula: int) -> bool:
        return self.session.query(UserEntity).filter(
            UserEntity.matricula == matricula
        ).count() > 0

    def find_by_matricula(self, matricula: int) -> Optional[User]:
        entity = self.session.query(UserEntity).filter(
            UserEntity.matricula == matricula
        ).first()
        return self.mapper.to_domain(entity) if entity else None