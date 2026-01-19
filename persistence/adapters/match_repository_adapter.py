from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.match_repository_port import MatchRepositoryPort
from domain.enums.match_status import MatchStatus
from domain.match import Match
from persistence.mappers.match_mapper import MatchMapper
from persistence.model.match_entity import MatchEntity


class MatchRepositoryAdapter(MatchRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: MatchMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[Match]:
        query = select(MatchEntity).where(
            MatchEntity.id == entity_id, MatchEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, match: Match) -> Match:
        entity = self.mapper.to_entity(match)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(MatchEntity.deleted_at.is_(None))
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_bracket(self, bracket_id: UUID) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.bracket_id == bracket_id,
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_team(self, team_id: UUID) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                or_(
                    MatchEntity.team1_id == team_id,
                    MatchEntity.team2_id == team_id,
                ),
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.desc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_status(self, status: MatchStatus) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.status == status.value,
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_in_progress_matches(self) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.status == MatchStatus.IN_PROGRESS.value,
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.started_at.desc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_scheduled_by_date(
        self, start_date: datetime, end_date: datetime
    ) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.status == MatchStatus.SCHEDULED.value,
                MatchEntity.scheduled_date >= start_date,
                MatchEntity.scheduled_date <= end_date,
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_bracket_group(self, bracket_group_id: UUID) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.bracket_group_id == bracket_group_id,
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        query = (
            update(MatchEntity)
            .where(
                MatchEntity.bracket_id == bracket_id,
                MatchEntity.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(), modified_at=datetime.now())
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount

    async def find_tbd_matches_by_bracket(self, bracket_id: UUID) -> List[Match]:
        query = (
            select(MatchEntity)
            .where(
                MatchEntity.bracket_id == bracket_id,
                or_(
                    MatchEntity.team1_id.is_(None),
                    MatchEntity.team2_id.is_(None),
                ),
                MatchEntity.deleted_at.is_(None),
            )
            .order_by(MatchEntity.scheduled_date.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]