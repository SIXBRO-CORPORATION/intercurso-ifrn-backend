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


def setup_extra_info_mocks(
    modality_repository, user_repository, team_member_repository, teams=()
):
    modality_repository.find_by_ids.return_value = [
        Modality(id=team.modality_id, name="Futsal", min_members=5, max_members=10)
        for team in teams
    ]
    user_repository.find_by_ids.return_value = [
        User(id=team.owner_id, name="Dono do Time") for team in teams if team.owner_id
    ]
    team_member_repository.count_by_teams.return_value = {team.id: 5 for team in teams}
    team_member_repository.count_pending_donations_by_teams.return_value = {
        team.id: 2 for team in teams
    }


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
        setup_extra_info_mocks(
            modality_repository, user_repository, team_member_repository, teams=[team]
        )

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
        assert extra_info[team.id]["modality_name"] == "Futsal"
        assert extra_info[team.id]["owner_name"] == "Dono do Time"

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
        team_repository.find_by_status_and_season_id.assert_not_called()

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

    async def test_monitor_filters_by_status_and_season_in_a_single_query(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        season_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), season_id=season_id)
        team_repository.find_by_status_and_season_id.return_value = [team]
        setup_extra_info_mocks(
            modality_repository, user_repository, team_member_repository, teams=[team]
        )

        context = make_context(requesting_user_role=UserRole.MONITOR)
        context.put_property("status", TeamStatus.SUBMITTED)
        context.put_property("season_id", season_id)

        result = await adapter.execute(context)

        assert result == [team]
        team_repository.find_by_status_and_season_id.assert_awaited_once_with(
            TeamStatus.SUBMITTED, season_id
        )
        team_repository.find_teams_by_status.assert_not_called()
        team_repository.find_by_season_id.assert_not_called()
        team_repository.find_all.assert_not_called()

    async def test_extra_info_is_loaded_in_batch_for_all_teams(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
        ) = make_adapter()
        modality_id = uuid4()
        owner_id = uuid4()
        team_a = Team(id=uuid4(), name="A", modality_id=modality_id, owner_id=owner_id)
        team_b = Team(id=uuid4(), name="B", modality_id=modality_id, owner_id=owner_id)
        team_c = Team(id=uuid4(), name="C", modality_id=uuid4(), owner_id=None)
        team_repository.find_all.return_value = [team_a, team_b, team_c]
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal", min_members=5, max_members=10)
        ]
        user_repository.find_by_ids.return_value = [User(id=owner_id, name="Dono")]
        team_member_repository.count_by_teams.return_value = {team_a.id: 6, team_b.id: 5}
        team_member_repository.count_pending_donations_by_teams.return_value = {
            team_a.id: 1
        }

        context = make_context(requesting_user_role=UserRole.MONITOR)
        await adapter.execute(context)

        modality_repository.find_by_ids.assert_awaited_once()
        assert sorted(modality_repository.find_by_ids.await_args.args[0]) == sorted(
            {modality_id, team_c.modality_id}
        )
        user_repository.find_by_ids.assert_awaited_once_with([owner_id])
        team_member_repository.count_by_teams.assert_awaited_once_with(
            [team_a.id, team_b.id, team_c.id]
        )
        team_member_repository.count_pending_donations_by_teams.assert_awaited_once()
        modality_repository.get.assert_not_called()
        user_repository.get.assert_not_called()
        team_member_repository.count_by_team.assert_not_called()

        info = context.get_property("team_extra_info", dict)
        assert info[team_a.id] == {
            "modality_name": "Futsal",
            "owner_name": "Dono",
            "members_count": 6,
            "donations_confirmed": 5,
            "donations_total": 6,
        }
        assert info[team_b.id]["donations_confirmed"] == 5
        assert info[team_c.id] == {
            "modality_name": None,
            "owner_name": None,
            "members_count": 0,
            "donations_confirmed": 0,
            "donations_total": 0,
        }

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
