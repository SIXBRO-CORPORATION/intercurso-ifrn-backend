from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from domain.season_modality import SeasonModality
from persistence.mappers.season_modality_mapper import SeasonModalityMapper
from persistence.model.season_modality_entity import SeasonModalityEntity


class SeasonModalityRepositoryAdapter(SeasonModalityRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: SeasonModalityMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[SeasonModality]:
        query = select(SeasonModalityEntity).where(
            SeasonModalityEntity.id == entity_id
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, season_modality: SeasonModality) -> SeasonModality:
        entity = self.mapper.to_entity(season_modality)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[SeasonModality]:
        query = select(SeasonModalityEntity).order_by(
            SeasonModalityEntity.created_at.desc()
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_season(self, season_id: UUID) -> List[SeasonModality]:
        query = select(SeasonModalityEntity).where(
            SeasonModalityEntity.season_id == season_id
        ).order_by(SeasonModalityEntity.created_at)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[SeasonModality]:
        query = select(SeasonModalityEntity).where(
            SeasonModalityEntity.season_id == season_id,
            SeasonModalityEntity.modality_id == modality_id,
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def exists_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> bool:
        query = select(SeasonModalityEntity.id).where(
            SeasonModalityEntity.season_id == season_id,
            SeasonModalityEntity.modality_id == modality_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def delete_by_season(self, season_id: UUID) -> int:
        query = delete(SeasonModalityEntity).where(
            SeasonModalityEntity.season_id == season_id
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount