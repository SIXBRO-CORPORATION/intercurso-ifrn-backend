import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from messaging.services.match_event_publisher import (
    MatchEventPublisher,
    MatchTeamSnapshot,
)
from domain.bracket.bracket import Bracket
from domain.enums.card_type import CardType
from domain.match.match import Match


def make_match(bracket_id=None) -> Match:
    return Match(id=uuid4(), bracket_id=bracket_id)


def make_publisher():
    broadcaster = AsyncMock()
    push_sender = AsyncMock()
    bracket_repository = AsyncMock()
    publisher = MatchEventPublisher(
        broadcaster=broadcaster,
        push_sender=push_sender,
        bracket_repository=bracket_repository,
    )
    return publisher, broadcaster, push_sender, bracket_repository


@pytest.mark.unit
class TestMatchEventPublisher:
    @pytest.mark.asyncio
    async def test_publish_broadcasts_to_match_channel(self):
        publisher, broadcaster, push_sender, bracket_repository = make_publisher()
        match = make_match()

        await publisher.publish(match, "clock_update", match_payload={"foo": "bar"})

        broadcaster.publish.assert_awaited_once()
        channel, event_type, payload = broadcaster.publish.call_args[0]
        assert channel == f"match:{match.id}"
        assert event_type == "clock_update"
        assert payload["event"] == "clock_update"
        assert payload["match_id"] == str(match.id)
        assert payload["match"] == {"foo": "bar"}
        push_sender.send_to_topic.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_accepts_multiple_event_types_and_broadcasts_each(self):
        publisher, broadcaster, _, _ = make_publisher()
        match = make_match()

        await publisher.publish(match, ("score_update", "goal_scored"), None)

        assert broadcaster.publish.await_count == 2
        event_types_broadcast = {
            call.args[1] for call in broadcaster.publish.await_args_list
        }
        assert event_types_broadcast == {"score_update", "goal_scored"}

    @pytest.mark.asyncio
    async def test_publish_fires_push_when_team_snapshots_and_push_content_exist(self):
        publisher, _, push_sender, _ = make_publisher()
        match = make_match()
        team1 = MatchTeamSnapshot(name="Time A", score=1)
        team2 = MatchTeamSnapshot(name="Time B", score=0)

        await publisher.publish(
            match, "goal_scored", None, team1=team1, team2=team2
        )
        # send_to_topic é disparado via asyncio.create_task (fire-and-forget);
        # cede o loop para a task rodar antes de inspecionar o mock.
        await asyncio.sleep(0)

        push_sender.send_to_topic.assert_awaited_once()
        topic, title, body, data = push_sender.send_to_topic.call_args[0]
        assert topic == "live_matches"
        assert title == "Gol!"
        assert "Time A" in body and "Time B" in body
        assert data == {"match_id": str(match.id), "event": "goal_scored"}

    @pytest.mark.asyncio
    async def test_publish_does_not_push_when_event_has_no_push_content(self):
        publisher, _, push_sender, _ = make_publisher()
        match = make_match()
        team1 = MatchTeamSnapshot(name="Time A", score=1)
        team2 = MatchTeamSnapshot(name="Time B", score=0)

        # "clock_update" não tem mapeamento em broadcast_push_content.
        await publisher.publish(
            match, "clock_update", None, team1=team1, team2=team2
        )
        await asyncio.sleep(0)

        push_sender.send_to_topic.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_does_not_push_when_team_snapshots_are_missing(self):
        publisher, _, push_sender, _ = make_publisher()
        match = make_match()

        await publisher.publish(match, "goal_scored", None)
        await asyncio.sleep(0)

        push_sender.send_to_topic.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_forwards_card_type_for_push_content(self):
        publisher, _, push_sender, _ = make_publisher()
        match = make_match()
        team1 = MatchTeamSnapshot(name="Time A", score=0)
        team2 = MatchTeamSnapshot(name="Time B", score=0)

        await publisher.publish(
            match,
            "card_issued",
            None,
            team1=team1,
            team2=team2,
            card_type=CardType.RED,
        )
        await asyncio.sleep(0)

        push_sender.send_to_topic.assert_awaited_once()
        title = push_sender.send_to_topic.call_args[0][1]
        assert title == "Cartão vermelho!"

    @pytest.mark.asyncio
    async def test_publish_does_not_push_for_yellow_card(self):
        publisher, _, push_sender, _ = make_publisher()
        match = make_match()
        team1 = MatchTeamSnapshot(name="Time A", score=0)
        team2 = MatchTeamSnapshot(name="Time B", score=0)

        await publisher.publish(
            match,
            "card_issued",
            None,
            team1=team1,
            team2=team2,
            card_type=CardType.YELLOW,
        )
        await asyncio.sleep(0)

        push_sender.send_to_topic.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_skips_season_channel_when_match_has_no_bracket(self):
        publisher, broadcaster, _, bracket_repository = make_publisher()
        match = make_match(bracket_id=None)

        await publisher.publish(match, "clock_update", None)

        bracket_repository.get.assert_not_called()
        assert broadcaster.publish.await_count == 1

    @pytest.mark.asyncio
    async def test_publish_skips_season_channel_when_bracket_has_no_season(self):
        publisher, broadcaster, _, bracket_repository = make_publisher()
        bracket_id = uuid4()
        match = make_match(bracket_id=bracket_id)
        bracket_repository.get.return_value = Bracket(id=bracket_id, season_id=None)

        await publisher.publish(match, "clock_update", None)

        bracket_repository.get.assert_awaited_once_with(bracket_id)
        assert broadcaster.publish.await_count == 1

    @pytest.mark.asyncio
    async def test_publish_skips_season_channel_when_bracket_not_found(self):
        publisher, broadcaster, _, bracket_repository = make_publisher()
        bracket_id = uuid4()
        match = make_match(bracket_id=bracket_id)
        bracket_repository.get.return_value = None

        await publisher.publish(match, "clock_update", None)

        assert broadcaster.publish.await_count == 1

    @pytest.mark.asyncio
    async def test_publish_also_broadcasts_to_season_channel_when_bracket_has_season(
        self,
    ):
        publisher, broadcaster, _, bracket_repository = make_publisher()
        bracket_id = uuid4()
        season_id = uuid4()
        match = make_match(bracket_id=bracket_id)
        bracket_repository.get.return_value = Bracket(
            id=bracket_id, season_id=season_id
        )

        await publisher.publish(match, "match_finished", None)

        assert broadcaster.publish.await_count == 2
        channels = {call.args[0] for call in broadcaster.publish.await_args_list}
        assert channels == {f"match:{match.id}", f"season:{season_id}"}
