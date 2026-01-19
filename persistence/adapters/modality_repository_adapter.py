from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.modality_repository_port import ModalityRepositoryPort
from domain.modality import Modality
from persistence.mappers.modality_mapper import ModalityMapper
from persistence.model.modality_entity import ModalityEntity


class ModalityRepositoryAdapter(ModalityRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: ModalityMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[Modality]:
        query = select(ModalityEntity).where(
            ModalityEntity.id == entity_id,
            ModalityEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, modality: Modality) -> Modality:
        entity = self.mapper.to_entity(modality)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[Modality]:
        query = select(ModalityEntity).where(
            ModalityEntity.deleted_at.is_(None)
        ).order_by(ModalityEntity.name)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_active_modalities(self) -> List[Modality]:
        query = select(ModalityEntity).where(
            ModalityEntity.active.is_(True),
            ModalityEntity.deleted_at.is_(None)
        ).order_by(ModalityEntity.name)
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def exists_by_id(self, modality_id: UUID) -> bool:
        query = select(ModalityEntity.id).where(
            ModalityEntity.id == modality_id,
            ModalityEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None