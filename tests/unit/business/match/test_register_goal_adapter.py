from uuid import uuid4

import pytest

from business.match.register_goal_adapter import RegisterGoalAdapter
from core.context import Context
from domain.enums.event_type import EventType
from domain.enums.match_status import MatchStatus
from domain.enums.score_type import ScoreType
from domain.enums.team_member_role import TeamMemberRole
from domain.exceptions.business_exception import BusinessException
from domain.bracket.bracket import Bracket
from domain.match.match_event import MatchEvent
from domain.modality.modality_configuration import ModalityConfiguration
from domain.team.team_member import TeamMember

from tests.unit.business.match._helpers import (
    make_adapter,
    make_in_progress_match,
    make_mocks,
    stub_empty_management_context,
)


def make_context(match_id, monitor_id, team_id, player_id):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    context.put_property("team_id", team_id)
    context.put_property("player_id", player_id)
    return context


def make_team_member(team_id, user_id):
    return TeamMember(id=uuid4(), team_id=team_id, user_id=user_id, role=TeamMemberRole.MEMBER)


class TestRegisterGoalAdapter:
    @pytest.mark.asyncio
    async def test_register_goal_success_soccer(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id, clock_seconds=100)

        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team1_id, player_id)
        ]
        mocks["match_event_repository"].find_by_match_and_type.return_value = []
        mocks["bracket_repository"].get.return_value = Bracket(
            id=match.bracket_id, modality_id=uuid4()
        )
        mocks["modality_repository"].get.return_value = None
        mocks["modality_configuration_repository"].find_by_modality.return_value = (
            ModalityConfiguration(score_type=ScoreType.GOALS)
        )

        context = make_context(match.id, monitor_id, match.team1_id, player_id)

        result = await adapter.execute(context)

        assert result.team1_score == 1
        assert result.team2_score == 0

        saved_event: MatchEvent = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.GOAL
        assert saved_event.player_id == player_id
        assert saved_event.team_id == match.team1_id

    @pytest.mark.asyncio
    async def test_register_point_for_volleyball_updates_set_metadata(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)

        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team2_id, player_id)
        ]
        mocks["match_event_repository"].find_by_match_and_type.return_value = []
        mocks["bracket_repository"].get.return_value = Bracket(
            id=match.bracket_id, modality_id=uuid4()
        )
        mocks["modality_repository"].get.return_value = None
        mocks["modality_configuration_repository"].find_by_modality.return_value = (
            ModalityConfiguration(score_type=ScoreType.SETS)
        )

        context = make_context(match.id, monitor_id, match.team2_id, player_id)

        result = await adapter.execute(context)

        saved_event: MatchEvent = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.POINT
        assert result.metadata_json["current_set_score"] == {"team1": 0, "team2": 1}

    @pytest.mark.asyncio
    async def test_blocks_when_match_not_in_progress(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.status = MatchStatus.SCHEDULED
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, monitor_id, match.team1_id, uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_monitor_is_not_responsible(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)

        match = make_in_progress_match(monitor_id=uuid4())
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, uuid4(), match.team1_id, uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_team_not_in_match(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, monitor_id, uuid4(), uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_player_not_in_team(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["team_member_repository"].find_members_by_team_id.return_value = []

        context = make_context(match.id, monitor_id, match.team1_id, uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_expelled_player(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterGoalAdapter, mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team1_id, player_id)
        ]
        mocks["match_event_repository"].find_by_match_and_type.return_value = [
            MatchEvent(match_id=match.id, player_id=player_id, event_type=EventType.EXPULSION)
        ]

        context = make_context(match.id, monitor_id, match.team1_id, player_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
