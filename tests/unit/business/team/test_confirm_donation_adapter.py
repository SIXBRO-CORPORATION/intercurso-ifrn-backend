from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    adapter = ConfirmDonationAdapter(
        team_repository, team_member_repository, user_repository
    )
    return adapter, team_repository, team_member_repository, user_repository


def make_context(team_id=None, target_user_id=None):
    context = Context()
    context.put_property("team_id", team_id if team_id is not None else uuid4())
    context.put_property(
        "target_user_id", target_user_id if target_user_id is not None else uuid4()
    )
    context.put_property("confirmed_by_user_id", uuid4())
    return context


@pytest.mark.unit
class TestConfirmDonationAdapter:
    async def test_confirms_donation_for_submitted_team_member(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        member_user = User(id=uuid4(), matricula="123456")
        member = TeamMember(
            id=uuid4(),
            user_id=member_user.id,
            donation_status=DonationStatus.PENDING_DONATION,
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = member_user
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_member_repository.save.return_value = member

        result = await adapter.execute(make_context(team.id))

        assert result.donation_status == DonationStatus.DONATION_CONFIRMED
        assert result.donation_confirmed_at is not None
        team_member_repository.save.assert_awaited_once()

    async def test_confirms_donation_for_approved_team_member(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.APPROVED)
        member_user = User(id=uuid4(), matricula="123456")
        member = TeamMember(
            id=uuid4(),
            user_id=member_user.id,
            donation_status=DonationStatus.PENDING_DONATION,
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = member_user
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_member_repository.save.return_value = member

        result = await adapter.execute(make_context(team.id))

        assert result.donation_status == DonationStatus.DONATION_CONFIRMED

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())

    async def test_blocks_when_team_status_invalid(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.DRAFT)
        team_repository.get.return_value = team

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_user_not_found(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        user_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

    async def test_blocks_when_user_is_not_a_team_member(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        member_user = User(id=uuid4(), matricula="123456")

        team_repository.get.return_value = team
        user_repository.get.return_value = member_user
        team_member_repository.find_members_by_team_id.return_value = []

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

    async def test_blocks_when_donation_already_confirmed(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        member_user = User(id=uuid4(), matricula="123456")
        member = TeamMember(
            id=uuid4(),
            user_id=member_user.id,
            donation_status=DonationStatus.DONATION_CONFIRMED,
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = member_user
        team_member_repository.find_members_by_team_id.return_value = [member]

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_team_id_or_target_user_id_missing(self):
        adapter, team_repository, team_member_repository, user_repository = (
            make_adapter()
        )

        context = Context()
        context.put_property("team_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.get.assert_not_awaited()
