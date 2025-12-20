from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.team import Team
from persistence.mappers.team_mapper import TeamMapper
from persistence.model.team_entity import TeamEntity
from persistence.model.team_member_entity import TeamMemberEntity


class TeamRepositoryAdapter(TeamRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: TeamMapper):
        self.session = session
        self.mapper = mapper

    async def get(self, team_id: UUID) -> Optional[Team]:
        selecionar = select(TeamEntity).where(TeamEntity.id == team_id)
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def save(self, team: Team) -> Team:
        entity = self.mapper.to_entity(team)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[Team]:
        selecionar = select(TeamEntity)
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def exists_by_id(self, team_id: UUID) -> bool:
        selecionar = select(TeamEntity).where(TeamEntity.id == team_id)
        result = await self.session.execute(selecionar)
        return result.scalar_one_or_none() is not None

    async def find_teams_by_matricula(self, matricula: int) -> List[Team]:
        selecionar = (
            select(TeamEntity)
            .join(TeamMemberEntity, TeamMemberEntity.team_id == TeamEntity.id)
            .where(TeamMemberEntity.member_matricula == matricula)
        )
        result = await self.session.execute(selecionar)
        team_entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in team_entities]

    async def find_teams_by_user_id(self, user_id: UUID) -> List[Team]:
        selecionar = (
            select(TeamEntity)
            .join(TeamMemberEntity, TeamMemberEntity.team_id == TeamEntity.id)
            .where(TeamMemberEntity.user_id == user_id)
        )
        result = await self.session.execute(selecionar)
        team_entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in team_entities]

    async def find_teams_by_status(self, status: TeamStatus) -> List[Team]:
        selecionar = (
            select(TeamEntity)
            .join(TeamMemberEntity, TeamMemberEntity.team_id == TeamEntity.id)
            .where(TeamMemberEntity.status == status)
        )
        result = await self.session.execute(selecionar)
        team_entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in team_entities]
