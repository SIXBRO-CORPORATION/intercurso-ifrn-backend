from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)
from persistence.mappers.volleyball_modality_configuration_mapper import (
    VolleyballModalityConfigurationMapper,
)
from persistence.model.volleyball_modality_configuration_entity import (
    VolleyballModalityConfigurationEntity,
)


class VolleyballModalityConfigurationRepositoryAdapter(
    VolleyballModalityConfigurationRepositoryPort
):
    def __init__(
        self, session: AsyncSession, mapper: VolleyballModalityConfigurationMapper
    ):
        self.session = session
        self.mapper = mapper

    async def get(
        self, entity_id: UUID
    ) -> Optional[VolleyballModalityConfiguration]:
        query = select(VolleyballModalityConfigurationEntity).where(
            VolleyballModalityConfigurationEntity.id == entity_id,
            VolleyballModalityConfigurationEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(
        self, volleyball_configuration: VolleyballModalityConfiguration
    ) -> VolleyballModalityConfiguration:
        entity = self.mapper.to_entity(volleyball_configuration)
        entity = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[VolleyballModalityConfiguration]:
        query = select(VolleyballModalityConfigurationEntity).where(
            VolleyballModalityConfigurationEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_modality_configuration_id(
        self, modality_configuration_id: UUID
    ) -> Optional[VolleyballModalityConfiguration]:
        query = select(VolleyballModalityConfigurationEntity).where(
            VolleyballModalityConfigurationEntity.modality_configuration_id
            == modality_configuration_id,
            VolleyballModalityConfigurationEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None
