from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.get_team_details_adapter import GetTeamDetailsAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    modality_repository = AsyncMock()

    adapter = GetTeamDetailsAdapter(
        team_repository, team_member_repository, user_repository, modality_repository
    )
    return adapter, team_repository, team_member_repository, user_repository, modality_repository


def make_context(team_id, requesting_user_id=None, requesting_user_role=UserRole.USER):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property(
        "requesting_user_id", requesting_user_id if requesting_user_id else uuid4()
    )
    context.put_property("requesting_user_role", requesting_user_role)
    return context


@pytest.mark.unit
class TestGetTeamDetailsAdapter:
    async def test_monitor_can_view_any_team(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        owner_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=owner_id)
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(team.id, requesting_user_role=UserRole.MONITOR)
        result = await adapter.execute(context)

        assert result is team
        team_member_repository.exists_by_team_and_user.assert_not_called()

    async def test_member_can_view_own_team(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        requesting_user_id = uuid4()
        owner_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=owner_id)
        member = TeamMember(
            id=uuid4(),
            team_id=team.id,
            user_id=requesting_user_id,
            role=TeamMemberRole.MEMBER,
            donation_status=DonationStatus.DONATION_CONFIRMED,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = [member]
        user_repository.find_by_ids.return_value = [
            User(id=requesting_user_id, name="Membro", matricula="123")
        ]
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(
            team.id, requesting_user_id=requesting_user_id, requesting_user_role=UserRole.USER
        )
        result = await adapter.execute(context)

        assert result is team
        members = context.get_property("members", list)
        assert len(members) == 1

    async def test_blocks_non_member_student(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=uuid4())
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = False

        context = make_context(team.id, requesting_user_role=UserRole.USER)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_team_not_found(self):
        (adapter, team_repository, *_rest) = make_adapter()
        team_repository.get.return_value = None

        context = make_context(uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_team_id_missing(self):
        (adapter, *_rest) = make_adapter()
        context = Context()
        context.put_property("requesting_user_id", uuid4())
        context.put_property("requesting_user_role", UserRole.USER)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
