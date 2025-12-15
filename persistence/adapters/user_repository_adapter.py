from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.commons.read_repository_port import T
from core.persistence.user_repository_port import UserRepositoryPort
from domain.user import User
from persistence.mappers.user_mapper import UserMapper
from persistence.model.user_entity import UserEntity


class UserRepositoryAdapter(UserRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: UserMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, user_id: UUID) -> Optional[User]:
        selecionar = select(UserEntity).where(UserEntity.id == user_id)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, user: User) -> User:
        entity = self.mapper.to_entity(user)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_by_email(self, email: str) -> Optional[User]:
        selecionar = select(UserEntity).where(UserEntity.email == email)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def exists_by_email(self, email: str) -> bool:
        selecionar = select(UserEntity.id).where(UserEntity.email == email)
        result = await self.session.execute(selecionar)
        return result.scalar_one_or_none() is not None

    async def exists_by_matricula(self, matricula: int) -> bool:
        selecionar = select(UserEntity.id).where(UserEntity.matricula == matricula)
        result = await self.session.execute(selecionar)
        return result.scalar_one_or_none() is not None

    async def find_by_matricula(self, matricula: int) -> Optional[User]:
        selecionar = select(UserEntity).where(UserEntity.matricula == matricula)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_all(self) -> List[T]:
        selecionar = select(UserEntity)
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]