from uuid import uuid4

import pytest

from business.match.register_card_adapter import RegisterCardAdapter
from core.context import Context
from domain.enums.card_type import CardType
from domain.enums.event_type import EventType
from domain.enums.team_member_role import TeamMemberRole
from domain.exceptions.business_exception import BusinessException
from domain.match.match_event import MatchEvent
from domain.team.team_member import TeamMember

from tests.unit.business.match._helpers import (
    make_adapter,
    make_in_progress_match,
    make_mocks,
    stub_empty_management_context,
)


def make_context(match_id, monitor_id, team_id, player_id, card_type):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    context.put_property("team_id", team_id)
    context.put_property("player_id", player_id)
    context.put_property("card_type", card_type)
    return context


def make_team_member(team_id, user_id):
    return TeamMember(id=uuid4(), team_id=team_id, user_id=user_id, role=TeamMemberRole.MEMBER)


class TestRegisterCardAdapter:
    @pytest.mark.asyncio
    async def test_first_yellow_card_does_not_expel(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterCardAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team1_id, player_id)
        ]
        mocks["match_event_repository"].find_by_match_and_type.return_value = []

        context = make_context(
            match.id, monitor_id, match.team1_id, player_id, CardType.YELLOW
        )

        await adapter.execute(context)

        saved_events = [
            call.args[0]
            for call in mocks["match_event_repository"].save.call_args_list
        ]
        assert len(saved_events) == 1
        assert saved_events[0].event_type == EventType.CARD_YELLOW

    @pytest.mark.asyncio
    async def test_second_yellow_card_triggers_automatic_expulsion(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterCardAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team1_id, player_id)
        ]

        # find_by_match_and_type é chamado 2x: 1) checar expulsão prévia
        # (EXPULSION) 2) contar amarelos anteriores (CARD_YELLOW).
        def find_by_type(match_id, event_type):
            if event_type == EventType.EXPULSION:
                return []
            if event_type == EventType.CARD_YELLOW:
                return [
                    MatchEvent(
                        match_id=match.id,
                        player_id=player_id,
                        event_type=EventType.CARD_YELLOW,
                    )
                ]
            return []

        mocks["match_event_repository"].find_by_match_and_type.side_effect = find_by_type

        context = make_context(
            match.id, monitor_id, match.team1_id, player_id, CardType.YELLOW
        )

        await adapter.execute(context)

        saved_events = [
            call.args[0]
            for call in mocks["match_event_repository"].save.call_args_list
        ]
        assert len(saved_events) == 2
        assert saved_events[0].event_type == EventType.CARD_YELLOW
        assert saved_events[1].event_type == EventType.EXPULSION
        assert saved_events[1].metadata_json["auto_generated"] is True

    @pytest.mark.asyncio
    async def test_direct_red_card_triggers_immediate_expulsion(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterCardAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        player_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["team_member_repository"].find_members_by_team_id.return_value = [
            make_team_member(match.team1_id, player_id)
        ]
        mocks["match_event_repository"].find_by_match_and_type.return_value = []

        context = make_context(
            match.id, monitor_id, match.team1_id, player_id, CardType.RED
        )

        await adapter.execute(context)

        saved_events = [
            call.args[0]
            for call in mocks["match_event_repository"].save.call_args_list
        ]
        assert len(saved_events) == 2
        assert saved_events[0].event_type == EventType.CARD_RED
        assert saved_events[1].event_type == EventType.EXPULSION
        assert saved_events[1].metadata_json["auto_generated"] is False

    @pytest.mark.asyncio
    async def test_blocks_card_for_already_expelled_player(self):
        mocks = make_mocks()
        adapter = make_adapter(RegisterCardAdapter, mocks)

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

        context = make_context(
            match.id, monitor_id, match.team1_id, player_id, CardType.YELLOW
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)
