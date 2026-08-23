from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.match.delete_event_adapter import DeleteEventAdapter
from business.match.undo_last_event_adapter import UndoLastEventAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.audit_action import AuditAction
from domain.enums.event_type import EventType
from domain.enums.match_status import MatchStatus
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.match.match_event import MatchEvent
from domain.match.match_set import MatchSet
from domain.modality.modality_configuration import ModalityConfiguration

from tests.unit.business.match._helpers import (
    make_in_progress_match,
    stub_empty_management_context,
)


def make_mocks():
    mocks = {
        "match_repository": AsyncMock(),
        "match_event_repository": AsyncMock(),
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
    mocks["match_event_repository"].soft_delete_event.return_value = True
    mocks["match_event_repository"].find_by_match_and_type.return_value = []
    mocks["match_set_repository"].count_sets_won_by_team.return_value = {}
    mocks["match_repository"].save.side_effect = lambda match: match
    # Sem modalidade de sets por padrão (futebol/handebol etc.).
    mocks["bracket_repository"].get.return_value = None
    mocks["modality_configuration_repository"].find_by_modality.return_value = None
    return mocks


def make_undo_adapter(mocks):
    return UndoLastEventAdapter(
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


def make_delete_adapter(mocks):
    return DeleteEventAdapter(
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


def setup_sets_modality(mocks):
    mocks["bracket_repository"].get.return_value = Bracket(
        id=uuid4(), modality_id=uuid4()
    )
    mocks["modality_configuration_repository"].find_by_modality.return_value = (
        ModalityConfiguration(id=uuid4(), score_type=ScoreType.SETS)
    )


def make_event(match_id, event_type, **kwargs):
    defaults = dict(
        id=uuid4(),
        match_id=match_id,
        created_at=datetime.now(),
        clock_seconds=100,
    )
    defaults.update(kwargs)
    return MatchEvent(event_type=event_type, **defaults)


def make_undo_context(match_id, monitor_id):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    return context


def make_delete_context(match_id, monitor_id, event_id):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    context.put_property("event_id", event_id)
    return context


class TestValidateMatchCorrectable:
    @pytest.mark.asyncio
    async def test_rejects_match_not_in_progress_nor_finished(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.status = MatchStatus.SCHEDULED
        mocks["match_repository"].get.return_value = match
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_undo_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_in_progress_match_requires_original_monitor(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)

        monitor_id = uuid4()
        other_monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["match_event_repository"].find_by_match.return_value = [
            make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        ]

        context = make_undo_context(match.id, other_monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_finished_match_allows_any_monitor(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)
        stub_empty_management_context(mocks)

        original_monitor_id = uuid4()
        other_monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=original_monitor_id)
        match.status = MatchStatus.FINISHED
        match.team1_score = 2
        match.team2_score = 1
        mocks["match_repository"].get.return_value = match
        mocks["match_event_repository"].find_by_match.return_value = [
            make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        ]

        context = make_undo_context(match.id, other_monitor_id)

        await adapter.execute(context)

        # Não levantou exceção: decisão 4.2 do handoff (qualquer Monitor
        # pode corrigir partida FINISHED).


class TestNonCorrectableEventTypes:
    @pytest.mark.asyncio
    async def test_undo_raises_when_only_structural_events_exist(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["match_event_repository"].find_by_match.return_value = [
            make_event(match.id, EventType.MATCH_STARTED),
            make_event(match.id, EventType.PERIOD_START),
        ]

        context = make_undo_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_delete_rejects_non_correctable_event_type(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        blocked_event = make_event(match.id, EventType.PERIOD_END)
        mocks["match_event_repository"].get.return_value = blocked_event

        context = make_delete_context(match.id, monitor_id, blocked_event.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        mocks["match_event_repository"].soft_delete_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_rejects_event_from_another_match(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        other_match_event = make_event(uuid4(), EventType.GOAL)
        mocks["match_event_repository"].get.return_value = other_match_event

        context = make_delete_context(match.id, monitor_id, other_match_event.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)


class TestUndoLastEvent:
    @pytest.mark.asyncio
    async def test_undo_picks_last_correctable_event_skipping_structural_ones(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 1
        mocks["match_repository"].get.return_value = match

        now = datetime.now()
        goal_event = make_event(
            match.id,
            EventType.GOAL,
            team_id=match.team1_id,
            created_at=now - timedelta(seconds=10),
        )
        period_end_event = make_event(
            match.id, EventType.PERIOD_END, created_at=now
        )
        mocks["match_event_repository"].find_by_match.side_effect = [
            [goal_event, period_end_event],  # 1ª chamada: localizar o alvo
            [period_end_event],  # 2ª chamada: recompute pós soft-delete
            [period_end_event],  # 3ª chamada: timeline em load_management_context
        ]

        context = make_undo_context(match.id, monitor_id)
        result = await adapter.execute(context)

        mocks["match_event_repository"].soft_delete_event.assert_awaited_once_with(
            goal_event.id
        )
        assert result.team1_score == 0

    @pytest.mark.asyncio
    async def test_undo_raises_when_no_events_exist(self):
        mocks = make_mocks()
        adapter = make_undo_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_undo_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)


class TestGoalPointRecomputation:
    @pytest.mark.asyncio
    async def test_deleting_goal_recomputes_running_score(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 2
        mocks["match_repository"].get.return_value = match

        goal_to_delete = make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        remaining_goal = make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        mocks["match_event_repository"].get.return_value = goal_to_delete
        # Após o soft delete, o evento removido não aparece mais em find_by_match.
        mocks["match_event_repository"].find_by_match.return_value = [remaining_goal]

        context = make_delete_context(match.id, monitor_id, goal_to_delete.id)
        result = await adapter.execute(context)

        assert result.team1_score == 1
        assert result.team2_score == 0

    @pytest.mark.asyncio
    async def test_delete_returns_business_error_when_event_already_corrected(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        goal_event = make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        mocks["match_event_repository"].get.return_value = goal_event
        mocks["match_event_repository"].soft_delete_event.return_value = False

        context = make_delete_context(match.id, monitor_id, goal_event.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)


class TestExpulsionReversal:
    @pytest.mark.asyncio
    async def test_deleting_expulsion_directly_reactivates_player(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        expulsion_event = make_event(
            match.id, EventType.EXPULSION, player_id=player_id
        )
        mocks["match_event_repository"].get.return_value = expulsion_event
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, expulsion_event.id)
        await adapter.execute(context)

        assert context.get_property("reactivated_player_id", type(player_id)) == (
            player_id
        )
        mocks["match_event_repository"].soft_delete_event.assert_awaited_once_with(
            expulsion_event.id
        )

    @pytest.mark.asyncio
    async def test_deleting_second_yellow_card_also_removes_linked_expulsion(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        second_yellow = make_event(
            match.id,
            EventType.CARD_YELLOW,
            player_id=player_id,
            clock_seconds=200,
            metadata_json={"previous_cards": 1},
        )
        linked_expulsion = make_event(
            match.id,
            EventType.EXPULSION,
            player_id=player_id,
            clock_seconds=200,
            metadata_json={"triggered_by": "second_yellow", "auto_generated": True},
        )
        mocks["match_event_repository"].get.return_value = second_yellow
        mocks["match_event_repository"].find_by_match_and_type.return_value = [
            linked_expulsion
        ]
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, second_yellow.id)
        await adapter.execute(context)

        assert mocks["match_event_repository"].soft_delete_event.await_args_list == [
            ((second_yellow.id,),),
            ((linked_expulsion.id,),),
        ]

    @pytest.mark.asyncio
    async def test_deleting_first_yellow_card_does_not_touch_expulsion(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        first_yellow = make_event(
            match.id,
            EventType.CARD_YELLOW,
            player_id=player_id,
            metadata_json={"previous_cards": 0},
        )
        mocks["match_event_repository"].get.return_value = first_yellow
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, first_yellow.id)
        await adapter.execute(context)

        mocks["match_event_repository"].soft_delete_event.assert_awaited_once_with(
            first_yellow.id
        )
        mocks["match_event_repository"].find_by_match_and_type.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_deleting_direct_red_card_removes_linked_expulsion(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match

        red_card = make_event(
            match.id, EventType.CARD_RED, player_id=player_id, clock_seconds=50
        )
        linked_expulsion = make_event(
            match.id,
            EventType.EXPULSION,
            player_id=player_id,
            clock_seconds=50,
            metadata_json={"triggered_by": "direct_red", "auto_generated": False},
        )
        mocks["match_event_repository"].get.return_value = red_card
        mocks["match_event_repository"].find_by_match_and_type.return_value = [
            linked_expulsion
        ]
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, red_card.id)
        await adapter.execute(context)

        assert mocks["match_event_repository"].soft_delete_event.await_count == 2


class TestSetEndCorrection:
    @pytest.mark.asyncio
    async def test_deleting_set_end_soft_deletes_match_set_and_recomputes(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)
        setup_sets_modality(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_sets_won = 1
        match.team2_sets_won = 0
        match.team1_score = 0
        match.team2_score = 0
        mocks["match_repository"].get.return_value = match

        set_end_event = make_event(
            match.id,
            EventType.SET_END,
            metadata_json={"set_number": 1},
        )
        match_set = MatchSet(
            id=uuid4(),
            match_id=match.id,
            set_number=1,
            team1_points=25,
            team2_points=20,
            winner_team_id=match.team1_id,
        )
        mocks["match_event_repository"].get.return_value = set_end_event
        mocks["match_set_repository"].find_by_match.return_value = [match_set]
        mocks["match_set_repository"].soft_delete_set.return_value = True
        # Depois do soft delete não sobra nenhum set ganho.
        mocks["match_set_repository"].count_sets_won_by_team.return_value = {}
        # Os pontos do set reaberto vêm dos GOAL/POINT restantes.
        reopened_point = make_event(match.id, EventType.POINT, team_id=match.team1_id)
        mocks["match_event_repository"].find_by_match.return_value = [reopened_point]

        context = make_delete_context(match.id, monitor_id, set_end_event.id)
        result = await adapter.execute(context)

        mocks["match_set_repository"].soft_delete_set.assert_awaited_once_with(
            match_set.id
        )
        assert result.team1_sets_won == 0
        assert result.team2_sets_won == 0
        assert result.team1_score == 1
        assert result.team2_score == 0


class TestPostFinishCorrection:
    @pytest.mark.asyncio
    async def test_correcting_finished_match_uses_special_audit_action(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.status = MatchStatus.FINISHED
        match.team1_score = 2
        match.team2_score = 1
        match.winner_id = match.team1_id
        mocks["match_repository"].get.return_value = match

        goal_event = make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        mocks["match_event_repository"].get.return_value = goal_event
        # Sobrou 1 gol do time 2, o placar vira 1x1 -> alerta de correção.
        remaining_goal = make_event(match.id, EventType.GOAL, team_id=match.team2_id)
        mocks["match_event_repository"].find_by_match.return_value = [remaining_goal]

        context = make_delete_context(match.id, monitor_id, goal_event.id)
        result = await adapter.execute(context)

        assert result.team1_score == 0
        assert result.team2_score == 1

        audit_call = mocks["audit_logger"].log.call_args
        assert audit_call.kwargs["action"] == AuditAction.MATCH_POST_FINISH_CORRECTION

        alert = context.get("correction_alert")
        assert alert is not None
        assert alert["alert_type"] == "CRITICAL"
        assert alert["previous_score"] == "2x1"
        assert alert["corrected_score"] == "0x1"

    @pytest.mark.asyncio
    async def test_correcting_finished_match_without_score_change_has_no_alert(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.status = MatchStatus.FINISHED
        match.team1_score = 2
        match.team2_score = 1
        mocks["match_repository"].get.return_value = match

        first_yellow = make_event(
            match.id,
            EventType.CARD_YELLOW,
            player_id=player_id,
            metadata_json={"previous_cards": 0},
        )
        mocks["match_event_repository"].get.return_value = first_yellow
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, first_yellow.id)
        await adapter.execute(context)

        audit_call = mocks["audit_logger"].log.call_args
        assert audit_call.kwargs["action"] == AuditAction.MATCH_POST_FINISH_CORRECTION
        assert context.get("correction_alert") is None

    @pytest.mark.asyncio
    async def test_correcting_in_progress_match_uses_normal_audit_action(self):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 1
        mocks["match_repository"].get.return_value = match

        goal_event = make_event(match.id, EventType.GOAL, team_id=match.team1_id)
        mocks["match_event_repository"].get.return_value = goal_event
        mocks["match_event_repository"].find_by_match.return_value = []

        context = make_delete_context(match.id, monitor_id, goal_event.id)
        await adapter.execute(context)

        audit_call = mocks["audit_logger"].log.call_args
        assert audit_call.kwargs["action"] == AuditAction.MATCH_EVENT_DELETED
        assert context.get("correction_alert") is None


class TestNonCorrectableStructuralDeletion:
    @pytest.mark.parametrize(
        "event_type",
        [
            EventType.MATCH_STARTED,
            EventType.MATCH_END,
            EventType.PERIOD_START,
            EventType.PERIOD_END,
        ],
    )
    @pytest.mark.asyncio
    async def test_cannot_delete_structural_event_types(self, event_type):
        mocks = make_mocks()
        adapter = make_delete_adapter(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        blocked_event = make_event(match.id, event_type)
        mocks["match_event_repository"].get.return_value = blocked_event

        context = make_delete_context(match.id, monitor_id, blocked_event.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
