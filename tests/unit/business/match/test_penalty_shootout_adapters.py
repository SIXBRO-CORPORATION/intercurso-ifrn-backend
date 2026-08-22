from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.match.end_penalty_shootout_adapter import EndPenaltyShootoutAdapter
from business.match.register_penalty_kick_adapter import RegisterPenaltyKickAdapter
from business.match.start_penalty_shootout_adapter import StartPenaltyShootoutAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.event_type import EventType
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.penalty_kick_result import PenaltyKickResult
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match

from tests.unit.business.match._helpers import stub_empty_management_context


def make_mocks():
    return {
        "match_repository": AsyncMock(),
        "match_event_repository": AsyncMock(),
        "bracket_group_team_repository": AsyncMock(),
        "team_repository": AsyncMock(),
        "team_member_repository": AsyncMock(),
        "user_repository": AsyncMock(),
        "bracket_repository": AsyncMock(),
        "modality_repository": AsyncMock(),
        "modality_configuration_repository": AsyncMock(),
        "volleyball_modality_configuration_repository": AsyncMock(),
        "match_set_repository": AsyncMock(),
        "audit_logger": AsyncMock(),
    }


def make_start_adapter(mocks):
    return StartPenaltyShootoutAdapter(
        mocks["match_repository"],
        mocks["match_event_repository"],
        mocks["team_repository"],
        mocks["team_member_repository"],
        mocks["user_repository"],
        mocks["bracket_repository"],
        mocks["modality_repository"],
        mocks["modality_configuration_repository"],
        mocks["volleyball_modality_configuration_repository"],
        mocks["match_set_repository"],
        mocks["audit_logger"],
    )


def make_register_kick_adapter(mocks):
    return RegisterPenaltyKickAdapter(
        mocks["match_repository"],
        mocks["match_event_repository"],
        mocks["team_repository"],
        mocks["team_member_repository"],
        mocks["user_repository"],
        mocks["bracket_repository"],
        mocks["modality_repository"],
        mocks["modality_configuration_repository"],
        mocks["volleyball_modality_configuration_repository"],
        mocks["match_set_repository"],
    )


def make_end_adapter(mocks):
    return EndPenaltyShootoutAdapter(
        mocks["match_repository"],
        mocks["match_event_repository"],
        mocks["bracket_group_team_repository"],
        mocks["team_repository"],
        mocks["team_member_repository"],
        mocks["user_repository"],
        mocks["bracket_repository"],
        mocks["modality_repository"],
        mocks["modality_configuration_repository"],
        mocks["volleyball_modality_configuration_repository"],
        mocks["match_set_repository"],
        mocks["audit_logger"],
    )


def make_match(
    match_category=MatchCategory.KNOCKOUT,
    team1_score=1,
    team2_score=1,
    monitor_id=None,
    penalty_shootout_active=False,
    team1_penalty_score=None,
    team2_penalty_score=None,
    team1_id=None,
    team2_id=None,
):
    return Match(
        id=uuid4(),
        bracket_id=uuid4(),
        team1_id=team1_id or uuid4(),
        team2_id=team2_id or uuid4(),
        monitor_id=monitor_id or uuid4(),
        match_type=MatchType.REGULAR,
        match_category=match_category,
        status=MatchStatus.IN_PROGRESS,
        team1_score=team1_score,
        team2_score=team2_score,
        penalty_shootout_active=penalty_shootout_active,
        team1_penalty_score=team1_penalty_score,
        team2_penalty_score=team2_penalty_score,
        clock_seconds=100,
        clock_running=False,
        current_period=1,
    )


def make_context(match_id, monitor_id, **extra_properties):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    for key, value in extra_properties.items():
        context.put_property(key, value)
    return context


class TestStartPenaltyShootoutAdapter:
    @pytest.mark.asyncio
    async def test_start_shootout_on_tied_knockout_match(self):
        mocks = make_mocks()
        stub_empty_management_context(mocks)
        adapter = make_start_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(team1_score=2, team2_score=2, monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        result = await adapter.execute(make_context(match.id, monitor_id))

        assert result.penalty_shootout_active is True
        assert result.team1_penalty_score == 0
        assert result.team2_penalty_score == 0
        mocks["audit_logger"].log.assert_awaited_once()
        assert (
            mocks["audit_logger"].log.await_args.kwargs["action"]
            == AuditAction.PENALTY_SHOOTOUT_STARTED
        )

    @pytest.mark.asyncio
    async def test_start_shootout_fails_when_not_tied(self):
        mocks = make_mocks()
        adapter = make_start_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(team1_score=2, team2_score=1, monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(match.id, monitor_id))

    @pytest.mark.asyncio
    async def test_start_shootout_fails_for_group_match(self):
        mocks = make_mocks()
        adapter = make_start_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            match_category=MatchCategory.GROUP,
            team1_score=1,
            team2_score=1,
            monitor_id=monitor_id,
        )
        mocks["match_repository"].get.return_value = match

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(match.id, monitor_id))

    @pytest.mark.asyncio
    async def test_start_shootout_fails_when_already_active(self):
        mocks = make_mocks()
        adapter = make_start_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            team1_score=1,
            team2_score=1,
            monitor_id=monitor_id,
            penalty_shootout_active=True,
        )
        mocks["match_repository"].get.return_value = match

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(match.id, monitor_id))


class TestRegisterPenaltyKickAdapter:
    @pytest.mark.asyncio
    async def test_register_goal_increments_penalty_score_and_creates_event(self):
        mocks = make_mocks()
        stub_empty_management_context(mocks)
        adapter = make_register_kick_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            monitor_id=monitor_id,
            penalty_shootout_active=True,
            team1_penalty_score=0,
            team2_penalty_score=0,
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(
            match.id,
            monitor_id,
            team_id=match.team1_id,
            player_id=None,
            result=PenaltyKickResult.GOAL,
        )
        result = await adapter.execute(context)

        assert result.team1_penalty_score == 1
        assert result.team2_penalty_score == 0

        mocks["match_event_repository"].save.assert_awaited_once()
        saved_event = mocks["match_event_repository"].save.await_args.args[0]
        assert saved_event.event_type == EventType.PENALTY_GOAL
        assert saved_event.team_id == match.team1_id

    @pytest.mark.asyncio
    async def test_register_miss_does_not_increment_penalty_score(self):
        mocks = make_mocks()
        stub_empty_management_context(mocks)
        adapter = make_register_kick_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            monitor_id=monitor_id,
            penalty_shootout_active=True,
            team1_penalty_score=0,
            team2_penalty_score=0,
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(
            match.id,
            monitor_id,
            team_id=match.team2_id,
            player_id=None,
            result=PenaltyKickResult.MISS,
        )
        result = await adapter.execute(context)

        assert result.team1_penalty_score == 0
        assert result.team2_penalty_score == 0

        saved_event = mocks["match_event_repository"].save.await_args.args[0]
        assert saved_event.event_type == EventType.PENALTY_MISS

    @pytest.mark.asyncio
    async def test_register_kick_fails_when_shootout_not_active(self):
        mocks = make_mocks()
        adapter = make_register_kick_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(monitor_id=monitor_id, penalty_shootout_active=False)
        mocks["match_repository"].get.return_value = match

        context = make_context(
            match.id,
            monitor_id,
            team_id=match.team1_id,
            player_id=None,
            result=PenaltyKickResult.GOAL,
        )
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_register_kick_fails_for_team_not_in_match(self):
        mocks = make_mocks()
        adapter = make_register_kick_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(monitor_id=monitor_id, penalty_shootout_active=True)
        mocks["match_repository"].get.return_value = match

        context = make_context(
            match.id,
            monitor_id,
            team_id=uuid4(),
            player_id=None,
            result=PenaltyKickResult.GOAL,
        )
        with pytest.raises(BusinessException):
            await adapter.execute(context)


class TestEndPenaltyShootoutAdapter:
    @pytest.mark.asyncio
    async def test_end_shootout_finishes_match_with_penalty_winner(self):
        mocks = make_mocks()
        stub_empty_management_context(mocks)
        adapter = make_end_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            team1_score=1,
            team2_score=1,
            monitor_id=monitor_id,
            penalty_shootout_active=True,
            team1_penalty_score=5,
            team2_penalty_score=4,
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        result = await adapter.execute(make_context(match.id, monitor_id))

        assert result.status == MatchStatus.FINISHED
        assert result.winner_id == match.team1_id
        assert result.penalty_shootout_active is False
        # placar oficial (tempo regulamentar) não é alterado pelos pênaltis
        assert result.team1_score == 1
        assert result.team2_score == 1
        assert result.penality_result == {
            "team1_penalties": 5,
            "team2_penalties": 4,
            "winner_id": str(match.team1_id),
        }

        mocks["match_event_repository"].save.assert_awaited_once()
        saved_event = mocks["match_event_repository"].save.await_args.args[0]
        assert saved_event.event_type == EventType.MATCH_END

        # MATCH_FINISHED é logado por finalize_match (compartilhado com o
        # finish_match_adapter sem pênaltis)
        mocks["audit_logger"].log.assert_awaited_once()
        assert (
            mocks["audit_logger"].log.await_args.kwargs["action"]
            == AuditAction.MATCH_FINISHED
        )

    @pytest.mark.asyncio
    async def test_end_shootout_fails_when_still_tied(self):
        mocks = make_mocks()
        adapter = make_end_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(
            monitor_id=monitor_id,
            penalty_shootout_active=True,
            team1_penalty_score=4,
            team2_penalty_score=4,
        )
        mocks["match_repository"].get.return_value = match

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(match.id, monitor_id))

        mocks["match_repository"].save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_end_shootout_fails_when_not_active(self):
        mocks = make_mocks()
        adapter = make_end_adapter(mocks)

        monitor_id = uuid4()
        match = make_match(monitor_id=monitor_id, penalty_shootout_active=False)
        mocks["match_repository"].get.return_value = match

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(match.id, monitor_id))

    @pytest.mark.asyncio
    async def test_end_shootout_advances_knockout_bracket_via_next_match_id(self):
        mocks = make_mocks()
        stub_empty_management_context(mocks)
        adapter = make_end_adapter(mocks)

        monitor_id = uuid4()
        next_match_id = uuid4()
        match = make_match(
            team1_score=0,
            team2_score=0,
            monitor_id=monitor_id,
            penalty_shootout_active=True,
            team1_penalty_score=3,
            team2_penalty_score=5,
        )
        match.next_match_id = next_match_id

        next_match = Match(
            id=next_match_id,
            bracket_id=match.bracket_id,
            match_type=MatchType.FINAL,
            match_category=MatchCategory.KNOCKOUT,
            status=MatchStatus.SCHEDULED,
            team1_id=None,
            team2_id=None,
        )

        async def get_match(match_id):
            return match if match_id == match.id else None

        async def lock_for_update(match_id):
            return next_match if match_id == next_match_id else None

        mocks["match_repository"].get.side_effect = get_match
        mocks["match_repository"].lock_for_update.side_effect = lock_for_update
        mocks["match_repository"].save.side_effect = lambda m: m

        await adapter.execute(make_context(match.id, monitor_id))

        assert next_match.team1_id == match.team2_id  # vencedor nos pênaltis
