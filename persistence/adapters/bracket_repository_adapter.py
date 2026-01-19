from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.bracket_repository_port import BracketRepositoryPort
from domain.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from persistence.mappers.bracket_mapper import BracketMapper
from persistence.model.bracket_entity import BracketEntity


class BracketRepositoryAdapter(BracketRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: BracketMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.id == entity_id,
            BracketEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, bracket: Bracket) -> Bracket:
        entity = self.mapper.to_entity(bracket)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.deleted_at.is_(None)
        ).order_by(BracketEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.season_id == season_id,
            BracketEntity.modality_id == modality_id,
            BracketEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_by_season(self, season_id: UUID) -> List[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.season_id == season_id,
            BracketEntity.deleted_at.is_(None)
        ).order_by(BracketEntity.created_at)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_status(self, status: BracketStatus) -> List[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.status == status.value,
            BracketEntity.deleted_at.is_(None)
        ).order_by(BracketEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def exists_active_bracket_for_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> bool:
        query = select(BracketEntity.id).where(
            BracketEntity.season_id == season_id,
            BracketEntity.modality_id == modality_id,
            BracketEntity.status == BracketStatus.ACTIVE.value,
            BracketEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def find_active_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[Bracket]:
        query = select(BracketEntity).where(
            BracketEntity.season_id == season_id,
            BracketEntity.modality_id == modality_id,
            BracketEntity.status == BracketStatus.ACTIVE.value,
            BracketEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None