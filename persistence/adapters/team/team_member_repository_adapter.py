from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from domain.enums.donation_status import DonationStatus
from domain.team.team_member import TeamMember
from persistence.mappers.team.team_member_mapper import TeamMemberMapper
from persistence.mappers.user.user_mapper import UserMapper
from persistence.model.team.team_member_entity import TeamMemberEntity


class TeamMemberRepositoryAdapter(TeamMemberRepositoryPort):
    def __init__(
        self,
        session: AsyncSession,
        team_member_mapper: TeamMemberMapper,
        user_mapper: UserMapper
    ):
        self.session = session
        self.team_member_mapper = team_member_mapper
        self.user_mapper = user_mapper

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
        entity = await self.session.merge(entity)
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

    async def find_by_team_and_user(
        self, team_id: UUID, user_id: UUID
    ) -> Optional[TeamMember]:
        selecionar = select(TeamMemberEntity).where(
            TeamMemberEntity.team_id == team_id,
            TeamMemberEntity.user_id == user_id,
            TeamMemberEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(selecionar)
        entity = result.scalar_one_or_none()
        return self.team_member_mapper.to_domain(entity) if entity else None

    async def exists_by_team_and_user(self, team_id: UUID, user_id: UUID) -> bool:
        selecionar = select(TeamMemberEntity.id).where(
            TeamMemberEntity.team_id == team_id,
            TeamMemberEntity.user_id == user_id,
            TeamMemberEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(selecionar)
        return result.scalar_one_or_none() is not None

    async def count_by_team(self, team_id: UUID) -> int:
        selecionar = select(func.count(TeamMemberEntity.id)).where(
            TeamMemberEntity.team_id == team_id,
            TeamMemberEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(selecionar)
        return result.scalar() or 0

    async def count_pending_donations_by_team(self, team_id: UUID) -> int:
        selecionar = select(func.count(TeamMemberEntity.id)).where(
            TeamMemberEntity.team_id == team_id,
            TeamMemberEntity.donation_status != DonationStatus.DONATION_CONFIRMED.value,
            TeamMemberEntity.deleted_at.is_(None),
        )
        result = await self.session.execute(selecionar)
        return result.scalar() or 0

    async def count_by_teams(self, team_ids: List[UUID]) -> Dict[UUID, int]:
        if not team_ids:
            return {}
        selecionar = (
            select(TeamMemberEntity.team_id, func.count(TeamMemberEntity.id))
            .where(
                TeamMemberEntity.team_id.in_(team_ids),
                TeamMemberEntity.deleted_at.is_(None),
            )
            .group_by(TeamMemberEntity.team_id)
        )
        result = await self.session.execute(selecionar)
        return {team_id: count for team_id, count in result.all()}

    async def count_pending_donations_by_teams(
        self, team_ids: List[UUID]
    ) -> Dict[UUID, int]:
        if not team_ids:
            return {}
        selecionar = (
            select(TeamMemberEntity.team_id, func.count(TeamMemberEntity.id))
            .where(
                TeamMemberEntity.team_id.in_(team_ids),
                TeamMemberEntity.donation_status
                != DonationStatus.DONATION_CONFIRMED.value,
                TeamMemberEntity.deleted_at.is_(None),
            )
            .group_by(TeamMemberEntity.team_id)
        )
        result = await self.session.execute(selecionar)
        return {team_id: count for team_id, count in result.all()}

    async def reset_donations_to_pending(self, team_id: UUID) -> int:
        statement = (
            update(TeamMemberEntity)
            .where(
                TeamMemberEntity.team_id == team_id,
                TeamMemberEntity.donation_status != DonationStatus.PENDING_DONATION.value,
                TeamMemberEntity.deleted_at.is_(None),
            )
            .values(
                donation_status=DonationStatus.PENDING_DONATION.value,
                modified_at=datetime.now(),
            )
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        return result.rowcount

    async def delete(self, team_member_id: UUID) -> int:
        statement = (
            update(TeamMemberEntity)
            .where(
                TeamMemberEntity.id == team_member_id,
                TeamMemberEntity.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(), modified_at=datetime.now())
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        return result.rowcount