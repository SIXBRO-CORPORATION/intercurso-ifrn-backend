from datetime import datetime
from typing import Dict, Optional, List, Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from domain.enums.event_type import EventType
from domain.match.match_event import MatchEvent
from persistence.mappers.match.match_event_mapper import MatchEventMapper
from persistence.model.match.match_event_entity import MatchEventEntity


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
        entity = await self.session.merge(entity)
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

    async def find_last_by_match_excluding_types(
        self, match_id: UUID, excluded_types: Sequence[EventType]
    ) -> Optional[MatchEvent]:
        query = select(MatchEventEntity).where(
            MatchEventEntity.match_id == match_id,
            MatchEventEntity.deleted_at.is_(None),
        )
        if excluded_types:
            query = query.where(
                MatchEventEntity.event_type.not_in(
                    [event_type.value for event_type in excluded_types]
                )
            )
        query = query.order_by(MatchEventEntity.created_at.desc()).limit(1)
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_last_by_match_and_type(
        self, match_id: UUID, event_type: EventType
    ) -> Optional[MatchEvent]:
        query = (
            select(MatchEventEntity)
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.event_type == event_type.value,
                MatchEventEntity.deleted_at.is_(None),
            )
            .order_by(MatchEventEntity.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_expulsion_by_player(
        self, match_id: UUID, player_id: UUID, preferred_clock_seconds: Optional[int]
    ) -> Optional[MatchEvent]:
        query = select(MatchEventEntity).where(
            MatchEventEntity.match_id == match_id,
            MatchEventEntity.player_id == player_id,
            MatchEventEntity.event_type == EventType.EXPULSION.value,
            MatchEventEntity.deleted_at.is_(None),
        )
        order_by = []
        if preferred_clock_seconds is not None:
            order_by.append(
                (MatchEventEntity.clock_seconds == preferred_clock_seconds).desc()
            )
        order_by.append(MatchEventEntity.clock_seconds.asc())
        result = await self.session.execute(query.order_by(*order_by).limit(1))
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def count_by_team(
        self,
        match_id: UUID,
        event_types: Sequence[EventType],
        created_after: Optional[datetime] = None,
    ) -> Dict[Optional[UUID], int]:
        query = (
            select(MatchEventEntity.team_id, func.count(MatchEventEntity.id))
            .where(
                MatchEventEntity.match_id == match_id,
                MatchEventEntity.event_type.in_(
                    [event_type.value for event_type in event_types]
                ),
                MatchEventEntity.deleted_at.is_(None),
            )
            .group_by(MatchEventEntity.team_id)
        )
        if created_after is not None:
            query = query.where(MatchEventEntity.created_at > created_after)
        result = await self.session.execute(query)
        return {team_id: count for team_id, count in result.all()}

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

    async def exists_by_match_player_and_type(
        self, match_id: UUID, player_id: UUID, event_type: EventType
    ) -> bool:
        query = select(MatchEventEntity.id).where(
            MatchEventEntity.match_id == match_id,
            MatchEventEntity.player_id == player_id,
            MatchEventEntity.event_type == event_type.value,
            MatchEventEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_by_match_player_and_type(
        self, match_id: UUID, player_id: UUID, event_type: EventType
    ) -> int:
        query = select(func.count(MatchEventEntity.id)).where(
            MatchEventEntity.match_id == match_id,
            MatchEventEntity.player_id == player_id,
            MatchEventEntity.event_type == event_type.value,
            MatchEventEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

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