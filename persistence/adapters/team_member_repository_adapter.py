from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from domain.team_member import TeamMember
from domain.user import User
from persistence.mappers.team_member_mapper import TeamMemberMapper
from persistence.mappers.user_mapper import UserMapper
from persistence.model.team_member_entity import TeamMemberEntity
from persistence.model.user_entity import UserEntity


class TeamMemberRepositoryAdapter(TeamMemberRepositoryPort):
    def __init__(self, session: AsyncSession, team_member_mapper: TeamMemberMapper, user_mapper: UserMapper):
        self.session = session
        self.team_member_mapper = team_member_mapper
        self.user_mapper = user_mapper

    async def save(self, team_member: TeamMember):
        entity = self.team_member_mapper.to_entity(team_member)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.team_member_mapper.to_domain(entity)

    async def find_members_by_team_id(self, team_id: UUID) -> List[User]:
        selecionar = (
            select(UserEntity)
            .join(
                TeamMemberEntity,
                UserEntity.matricula == TeamMemberEntity.member_matricula
            )
            .where(
                TeamMemberEntity.team_id == team_id
            )
        )

        result = await self.session.execute(selecionar)
        user_entities = result.scalars().all()

        return [self.user_mapper.to_domain(entity) for entity in user_entities]