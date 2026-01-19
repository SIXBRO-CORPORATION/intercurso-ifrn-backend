from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from domain.team_member import TeamMember
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.model.team_member_entity import TeamMemberEntity


class TeamMemberRepositoryAdapter(TeamMemberRepositoryPort):
    def __init__(
        self,
        session: AsyncSession,
        team_member_mapper: TeamMemberMapper,
    ):
        self.session = session
        self.team_member_mapper = team_member_mapper

    async def get(self, entity_id: UUID) -> Optional[TeamMember]:
        selecionar = select(TeamMemberEntity).where(
            TeamMemberEntity.id == entity_id,
            TeamMemberEntity.deleted_at.is_(None)
        )
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.team_member_mapper.to_domain(entity) if entity else None

    async def save(self, team_member: TeamMember) -> TeamMember:
        entity = self.team_member_mapper.to_entity(team_member)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.team_member_mapper.to_domain(entity)

    async def find_all(self) -> List[TeamMember]:
        selecionar = select(TeamMemberEntity).where(
            TeamMemberEntity.deleted_at.is_(None)
        ).order_by(TeamMemberEntity.joined_at.desc())
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.team_member_mapper.to_domain(entity) for entity in entities]

    async def find_members_by_team_id(self, team_id: UUID) -> List[TeamMember]:
        selecionar = select(TeamMemberEntity).where(
            TeamMemberEntity.team_id == team_id,
            TeamMemberEntity.deleted_at.is_(None)
        ).order_by(TeamMemberEntity.joined_at)

        result = await self.session.execute(selecionar)
        team_member_entities = result.scalars().all()

        return [
            self.team_member_mapper.to_domain(entity) for entity in team_member_entities
        ]