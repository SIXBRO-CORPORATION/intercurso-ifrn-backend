from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.list_teams_adapter import ListTeamsAdapter
from core.context import Context
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.team.team import Team
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    modality_repository = AsyncMock()

    adapter = ListTeamsAdapter(
        team_repository, team_member_repository, user_repository, modality_repository
    )
    return adapter, team_repository, team_member_repository, user_repository, modality_repository


def make_context(requesting_user_id=None, requesting_user_role=UserRole.USER):
    context = Context()
    context.put_property(
        "requesting_user_id", requesting_user_id if requesting_user_id else uuid4()
    )
    context.put_property("requesting_user_role", requesting_user_role)
    return context


def setup_extra_info_mocks(modality_repository, user_repository, team_member_repository):
    modality_repository.get.return_value = Modality(
        id=uuid4(), name="Futsal", min_members=5, max_members=10
    )
    user_repository.get.return_value = User(id=uuid4(), name="Dono do Time")
    team_member_repository.count_by_team.return_value = 5
    team_member_repository.count_pending_donations_by_team.return_value = 2


@pytest.mark.unit
class TestListTeamsAdapter:
    async def test_student_only_sees_own_teams(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        requesting_user_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=uuid4())
        team_repository.find_teams_by_user_id.return_value = [team]
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_id, UserRole.USER)
        result = await adapter.execute(context)

        assert result == [team]
        team_repository.find_teams_by_user_id.assert_awaited_once_with(
            requesting_user_id
        )
        team_repository.find_all.assert_not_called()
        team_repository.find_teams_by_status.assert_not_called()

        extra_info = context.get_property("team_extra_info", dict)
        assert extra_info[team.id]["members_count"] == 5
        assert extra_info[team.id]["donations_confirmed"] == 3

    async def test_student_filters_are_ignored(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        team_repository.find_teams_by_user_id.return_value = []
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_role=UserRole.USER)
        context.put_property("status", TeamStatus.SUBMITTED)
        context.put_property("season_id", uuid4())

        await adapter.execute(context)

        team_repository.find_teams_by_status.assert_not_called()
        team_repository.find_by_season_id.assert_not_called()

    async def test_monitor_lists_all_teams_without_filters(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        team_repository.find_all.return_value = []
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_role=UserRole.MONITOR)
        await adapter.execute(context)

        team_repository.find_all.assert_awaited_once()

    async def test_monitor_filters_by_status(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        team_repository.find_teams_by_status.return_value = []
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_role=UserRole.MONITOR)
        context.put_property("status", TeamStatus.SUBMITTED)

        await adapter.execute(context)

        team_repository.find_teams_by_status.assert_awaited_once_with(
            TeamStatus.SUBMITTED
        )
        team_repository.find_all.assert_not_called()

    async def test_monitor_filters_by_season_when_status_not_informed(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        season_id = uuid4()
        team_repository.find_by_season_id.return_value = []
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_role=UserRole.MONITOR)
        context.put_property("season_id", season_id)

        await adapter.execute(context)

        team_repository.find_by_season_id.assert_awaited_once_with(season_id)

    async def test_admin_is_treated_as_monitor(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        team_repository.find_all.return_value = []
        setup_extra_info_mocks(modality_repository, user_repository, team_member_repository)

        context = make_context(requesting_user_role=UserRole.ADMIN)
        await adapter.execute(context)

        team_repository.find_all.assert_awaited_once()
        team_repository.find_teams_by_user_id.assert_not_called()

    async def test_blocks_when_requesting_user_missing(self):
        (adapter, *_rest) = make_adapter()

        with pytest.raises(BusinessException):
            await adapter.execute(Context())
