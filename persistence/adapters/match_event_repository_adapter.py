from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from domain.enums.event_type import EventType
from domain.match_event import MatchEvent
from persistence.mappers.match_event_mapper import MatchEventMapper
from persistence.model.match_event_entity import MatchEventEntity


class MatchEventRepositoryAdapter(MatchEventRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: MatchEventMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[MatchEvent]:
        query = select(MatchEventEntity).where(
            MatchEventEntity.id == entity_id,
            MatchEventEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, match_event: MatchEvent) -> MatchEvent:
        entity = self.mapper.to_entity(match_event)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[MatchEvent]:
        query = select(MatchEventEntity).where(
            MatchEventEntity.deleted_at.is_(None)
        ).order_by(MatchEventEntity.created_at.desc())
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_match(self, match_id: UUID) -> List[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.clock_seconds.asc(), MatchEventEntity.created_at.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_match_and_type(
        self, match_id: UUID, event_type: EventType
    ) -> List[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.event_type == event_type.value,
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.clock_seconds.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_player(self, player_id: UUID) -> List[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.player_id == player_id,
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.created_at.desc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_active_by_match(self, match_id: UUID) -> List[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.active.is_(True),
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.clock_seconds.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_last_event_by_match(self, match_id: UUID) -> Optional[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def soft_delete_event(self, event_id: UUID) -> bool:
        query = (
            update(MatchEventEntity)
            .where(
                MatchEventEntity.id == event_id,
                MatchEventEntity.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(), modified_at=datetime.now())
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount > 0