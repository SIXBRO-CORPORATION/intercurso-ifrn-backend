from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from domain.bracket_group_team import BracketGroupTeam
from persistence.mappers.bracket_group_team_mapper import BracketGroupTeamMapper
from persistence.model.bracket_group_entity import BracketGroupEntity
from persistence.model.bracket_group_team_entity import BracketGroupTeamEntity


class BracketGroupTeamRepositoryAdapter(BracketGroupTeamRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: BracketGroupTeamMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, entity_id: UUID) -> Optional[BracketGroupTeam]:
        query = select(BracketGroupTeamEntity).where(
            BracketGroupTeamEntity.id == entity_id,
            BracketGroupTeamEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, bracket_group_team: BracketGroupTeam) -> BracketGroupTeam:
        entity = self.mapper.to_entity(bracket_group_team)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[BracketGroupTeam]:
        query = (
            select(BracketGroupTeamEntity)
            .where(BracketGroupTeamEntity.deleted_at.is_(None))
            .order_by(BracketGroupTeamEntity.points.desc())
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_group(self, bracket_group_id: UUID) -> List[BracketGroupTeam]:
        query = (
            select(BracketGroupTeamEntity)
            .where(
                BracketGroupTeamEntity.bracket_group_id == bracket_group_id,
                BracketGroupTeamEntity.deleted_at.is_(None),
            )
            .order_by(
                BracketGroupTeamEntity.points.desc(),
                BracketGroupTeamEntity.goals_difference.desc(),
                BracketGroupTeamEntity.goals_for.desc(),
            )
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_bracket_group_and_team(
        self, bracket_group_id: UUID, team_id: UUID
    ) -> Optional[BracketGroupTeam]:
        query = select(BracketGroupTeamEntity).where(
            BracketGroupTeamEntity.bracket_group_id == bracket_group_id,
            BracketGroupTeamEntity.team_id == team_id,
            BracketGroupTeamEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        groups_query = select(BracketGroupEntity.id).where(
            BracketGroupEntity.bracket_id == bracket_id,
            BracketGroupEntity.deleted_at.is_(None),
        )
        groups_result = await self.session.execute(groups_query)
        group_ids = [row[0] for row in groups_result.all()]

        if not group_ids:
            return 0

        query = (
            update(BracketGroupTeamEntity)
            .where(
                BracketGroupTeamEntity.bracket_group_id.in_(group_ids),
                BracketGroupTeamEntity.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(), modified_at=datetime.now())
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount