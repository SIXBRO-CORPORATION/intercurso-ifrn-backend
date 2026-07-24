from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.approve_team_adapter import ApproveTeamAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team
from domain.team.team_member import TeamMember


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    adapter = ApproveTeamAdapter(team_repository, team_member_repository)
    return adapter, team_repository, team_member_repository


def make_context(team_id=None):
    context = Context()
    context.put_property("team_id", team_id if team_id is not None else uuid4())
    context.put_property("approved_by_user_id", uuid4())
    return context


def make_member(donation_status=DonationStatus.DONATION_CONFIRMED):
    return TeamMember(id=uuid4(), user_id=uuid4(), donation_status=donation_status)


@pytest.mark.unit
class TestApproveTeamAdapter:
    async def test_approves_submitted_team_with_all_donations_confirmed(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        members = [make_member(), make_member()]

        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = members
        team_repository.save.return_value = team

        result = await adapter.execute(make_context(team.id))

        assert result.status == TeamStatus.APPROVED
        assert result.approved_at is not None
        team_repository.save.assert_awaited_once()

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())

    async def test_blocks_when_team_not_submitted(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.DRAFT)
        team_repository.get.return_value = team

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_has_no_members(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = []

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_pending_donation_exists(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        members = [
            make_member(),
            make_member(donation_status=DonationStatus.PENDING_DONATION),
        ]
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = members

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_id_is_missing(self):
        adapter, team_repository, team_member_repository = make_adapter()

        context = Context()
        context.put_property("approved_by_user_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.get.assert_not_awaited()
