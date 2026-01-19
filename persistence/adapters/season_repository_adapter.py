from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.season import Season
from persistence.mappers.season_mapper import SeasonMapper
from persistence.model.season_entity import SeasonEntity


class SeasonRepositoryAdapter(SeasonRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: SeasonMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[Season]:
        query = select(SeasonEntity).where(
            SeasonEntity.id == entity_id,
            SeasonEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, season: Season) -> Season:
        entity = self.mapper.to_entity(season)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[Season]:
        query = select(SeasonEntity).where(
            SeasonEntity.deleted_at.is_(None)
        ).order_by(SeasonEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_active_season(self) -> Optional[Season]:
        query = select(SeasonEntity).where(
            SeasonEntity.active.is_(True),
            SeasonEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_by_status(self, status: SeasonStatus) -> List[Season]:
        query = select(SeasonEntity).where(
            SeasonEntity.status == status.value,
            SeasonEntity.deleted_at.is_(None)
        ).order_by(SeasonEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_year(self, year: int) -> List[Season]:
        query = select(SeasonEntity).where(
            SeasonEntity.year == year,
            SeasonEntity.deleted_at.is_(None)
        ).order_by(SeasonEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def exists_active_season(self) -> bool:
        query = select(SeasonEntity.id).where(
            SeasonEntity.active.is_(True),
            SeasonEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None