from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from domain.modality_configuration import ModalityConfiguration
from persistence.mappers.modality_configuration_mapper import (
    ModalityConfigurationMapper,
)
from persistence.model.modality_configuration_entity import (
    ModalityConfigurationEntity,
)


class ModalityConfigurationRepositoryAdapter(ModalityConfigurationRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: ModalityConfigurationMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[ModalityConfiguration]:
        query = select(ModalityConfigurationEntity).where(
            ModalityConfigurationEntity.id == entity_id,
            ModalityConfigurationEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(
        self, modality_config: ModalityConfiguration
    ) -> ModalityConfiguration:
        entity = self.mapper.to_entity(modality_config)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[ModalityConfiguration]:
        query = select(ModalityConfigurationEntity).where(
            ModalityConfigurationEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_season_modality(
        self, season_modality_id: UUID
    ) -> Optional[ModalityConfiguration]:
        query = select(ModalityConfigurationEntity).where(
            ModalityConfigurationEntity.season_modality_id == season_modality_id,
            ModalityConfigurationEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def exists_by_season_modality(self, season_modality_id: UUID) -> bool:
        query = select(ModalityConfigurationEntity.id).where(
            ModalityConfigurationEntity.season_modality_id == season_modality_id,
            ModalityConfigurationEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None