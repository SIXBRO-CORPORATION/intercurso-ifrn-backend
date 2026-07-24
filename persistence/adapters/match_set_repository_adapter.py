from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.match_set_repository_port import MatchSetRepositoryPort
from domain.match.match_set import MatchSet
from persistence.mappers.match_set_mapper import MatchSetMapper
from persistence.model.match_set_entity import MatchSetEntity


class MatchSetRepositoryAdapter(MatchSetRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: MatchSetMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[MatchSet]:
        query = select(MatchSetEntity).where(
            MatchSetEntity.id == entity_id,
            MatchSetEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, match_set: MatchSet) -> MatchSet:
        entity = self.mapper.to_entity(match_set)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[MatchSet]:
        query = select(MatchSetEntity).where(MatchSetEntity.deleted_at.is_(None))
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_match(self, match_id: UUID) -> List[MatchSet]:
        query = (
            select(MatchSetEntity)
            .where(
                MatchSetEntity.match_id == match_id,
                MatchSetEntity.deleted_at.is_(None),
            )
            .order_by(MatchSetEntity.set_number.asc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def count_sets_won_by_team(self, match_id: UUID) -> dict:
        query = (
            select(MatchSetEntity.winner_team_id, func.count(MatchSetEntity.id))
            .where(
                MatchSetEntity.match_id == match_id,
                MatchSetEntity.deleted_at.is_(None),
            )
            .group_by(MatchSetEntity.winner_team_id)
        )
        result = await self.session.execute(query)
        return {winner_team_id: count for winner_team_id, count in result.all()}
