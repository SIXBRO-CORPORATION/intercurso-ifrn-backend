import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.season.season import Season
from messaging.season_broadcast_content import (
    SEASON_TOPIC,
    registration_opened_content,
    season_finished_content,
)
from messaging.services.season_broadcast_notifier import SeasonBroadcastNotifier


async def _drain() -> None:
    for _ in range(3):
        await asyncio.sleep(0)


def make_notifier():
    push_sender = AsyncMock()
    return SeasonBroadcastNotifier(push_sender=push_sender), push_sender


@pytest.mark.unit
class TestSeasonBroadcastNotifier:

    async def test_sends_to_season_topic_with_season_data(self):
        notifier, push_sender = make_notifier()
        season = Season(id=uuid4(), name="Intercurso 2026")

        await notifier.season_finished(season)
        await _drain()

        push_sender.send_to_topic.assert_awaited_once()
        topic, title, body, data = push_sender.send_to_topic.await_args.args
        assert topic == SEASON_TOPIC
        assert title == "Temporada encerrada"
        assert "Intercurso 2026" in body
        assert data == {"season_id": str(season.id), "event": "season_finished"}

    async def test_never_uses_per_user_send(self):
        notifier, push_sender = make_notifier()

        await notifier.registration_closed(Season(id=uuid4(), name="X"))
        await _drain()

        push_sender.send.assert_not_awaited()

    async def test_send_failure_is_swallowed(self):
        notifier, push_sender = make_notifier()
        push_sender.send_to_topic.side_effect = RuntimeError("fcm down")

        await notifier.registration_opened(Season(id=uuid4(), name="X"))
        await _drain()

        push_sender.send_to_topic.assert_awaited_once()

    async def test_pending_tasks_are_released_after_completion(self):
        notifier, _ = make_notifier()

        await notifier.season_finished(Season(id=uuid4(), name="X"))
        await _drain()

        assert notifier._pending_tasks == set()


class TestSeasonBroadcastContent:

    def test_opened_content_formats_end_date_in_rn_local_time(self):
        end = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)

        title, body = registration_opened_content("Intercurso 2026", end)

        assert title == "Inscrições abertas!"
        assert "10/11/2026 às 12:00" in body

    def test_opened_content_without_end_date(self):
        title, body = registration_opened_content("Intercurso 2026", None)

        assert "até" not in body
        assert "Intercurso 2026" in body

    def test_finished_content(self):
        title, body = season_finished_content("Intercurso 2026")

        assert title == "Temporada encerrada"
        assert "Intercurso 2026" in body
