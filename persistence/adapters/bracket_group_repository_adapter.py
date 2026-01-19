from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.bracket_group_repository_port import BracketGroupRepositoryPort
from domain.bracket_group import BracketGroup
from persistence.mappers.bracket_group_mapper import BracketGroupMapper
from persistence.model.bracket_group_entity import BracketGroupEntity


class BracketGroupRepositoryAdapter(BracketGroupRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: BracketGroupMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[BracketGroup]:
        query = select(BracketGroupEntity).where(
            BracketGroupEntity.id == entity_id,
            BracketGroupEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, bracket_group: BracketGroup) -> BracketGroup:
        entity = self.mapper.to_entity(bracket_group)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[BracketGroup]:
        query = select(BracketGroupEntity).where(
            BracketGroupEntity.deleted_at.is_(None)
        ).order_by(BracketGroupEntity.display_order)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_bracket(self, bracket_id: UUID) -> List[BracketGroup]:
        query = select(BracketGroupEntity).where(
            BracketGroupEntity.bracket_id == bracket_id,
            BracketGroupEntity.deleted_at.is_(None)
        ).order_by(BracketGroupEntity.display_order)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        query = (
            update(BracketGroupEntity)
            .where(
                BracketGroupEntity.bracket_id == bracket_id,
                BracketGroupEntity.deleted_at.is_(None)
            )
            .values(deleted_at=datetime.now(), modified_at=datetime.now())
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount