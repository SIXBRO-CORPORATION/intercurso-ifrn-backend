from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.commons.read_repository_port import T
from core.persistence.messaging.device_token_repository_port import (
    DeviceTokenRepositoryPort,
)
from domain.messaging.device_token import DeviceToken
from persistence.mappers.messaging.device_token_mapper import DeviceTokenMapper
from persistence.model.messaging.device_token_entity import DeviceTokenEntity


class DeviceTokenRepositoryAdapter(DeviceTokenRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: DeviceTokenMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[DeviceToken]:
        selecionar = select(DeviceTokenEntity).where(DeviceTokenEntity.id == entity_id)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, device_token: DeviceToken) -> DeviceToken:
        entity = self.mapper.to_entity(device_token)
        entity = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[T]:
        selecionar = select(DeviceTokenEntity)
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_token(self, token: str) -> Optional[DeviceToken]:
        selecionar = select(DeviceTokenEntity).where(DeviceTokenEntity.token == token)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_active_by_user(self, user_id: UUID) -> List[DeviceToken]:
        selecionar = select(DeviceTokenEntity).where(
            DeviceTokenEntity.user_id == user_id,
            DeviceTokenEntity.active.is_(True),
        )
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_active_by_users(self, user_ids: List[UUID]) -> List[DeviceToken]:
        if not user_ids:
            return []
        selecionar = select(DeviceTokenEntity).where(
            DeviceTokenEntity.user_id.in_(user_ids),
            DeviceTokenEntity.active.is_(True),
        )
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def deactivate_by_token(self, token: str) -> None:
        query = (
            update(DeviceTokenEntity)
            .where(DeviceTokenEntity.token == token)
            .values(active=False)
        )
        await self.session.execute(query)
        await self.session.flush()
