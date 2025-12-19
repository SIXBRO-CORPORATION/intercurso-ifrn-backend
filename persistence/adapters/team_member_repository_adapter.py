from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from domain.team_member import TeamMember
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper
from persistence.model.team_member_entity import TeamMemberEntity


class TeamMemberRepositoryAdapter(TeamMemberRepositoryPort):
    def __init__(
        self,
        session: AsyncSession,
        team_member_mapper: TeamMemberMapper,
        user_mapper: UserMapper,
    ):
        self.session = session
        self.team_member_mapper = team_member_mapper
        self.user_mapper = user_mapper

    async def save(self, team_member: TeamMember):
        entity = self.team_member_mapper.to_entity(team_member)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.team_member_mapper.to_domain(entity)

    async def find_members_by_team_id(self, team_id: UUID) -> List[TeamMember]:
        selecionar = select(TeamMemberEntity).where(TeamMemberEntity.team_id == team_id)

        result = await self.session.execute(selecionar)
        team_member_entities = result.scalars().all()

        return [
            self.team_member_mapper.to_domain(entity) for entity in team_member_entities
        ]

    async def find_member_by_matricula_and_team_id(
        self, matricula: int, team_id: UUID
    ) -> Optional[TeamMember]:
        selecionar = select(TeamMemberEntity).where(
            TeamMemberEntity.member_matricula == matricula,
            TeamMemberEntity.team_id == team_id,
        )

        result = await self.session.execute(selecionar)
        entity = result.scalars().first()
        return self.team_member_mapper.to_domain(entity)
