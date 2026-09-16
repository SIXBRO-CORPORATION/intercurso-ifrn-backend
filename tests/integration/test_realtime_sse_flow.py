
import asyncio
import json
import threading
import time
from datetime import datetime
from uuid import uuid4

import pytest
import uvicorn
from httpx import AsyncClient

from core.realtime.broadcaster import get_broadcaster_singleton
from domain.enums.user_role import UserRole
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.score_type import ScoreType
from domain.match.match import Match
from domain.bracket.bracket import Bracket
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.team.team import Team
from domain.user.user import User
from web.dependencies import (
    get_bracket_repository,
    get_match_event_repository,
    get_match_repository,
    get_match_set_repository,
    get_modality_configuration_repository,
    get_modality_repository,
    require_authenticated_user,
    get_team_member_repository,
    get_team_repository,
    get_user_repository,
    get_volleyball_modality_configuration_repository,
)
from web.main import app


class _FakeMatchRepository:
    def __init__(self, matches: list[Match]):
        self._matches = {m.id: m for m in matches}

    async def get(self, entity_id):
        return self._matches.get(entity_id)


class _PublishingMatchRepository(_FakeMatchRepository):
    def __init__(self, matches, publish_event):
        super().__init__(matches)
        self._publish_event = publish_event
        self._get_count = 0

    async def get(self, entity_id):
        self._get_count += 1
        match = await super().get(entity_id)
        if self._get_count == 3:
            await self._publish_event()
        return match


class _FakeStateRepository:
    def __init__(self, values=None):
        self._values = values or {}

    async def get(self, entity_id):
        return self._values.get(entity_id)

    async def find_members_by_team_id(self, team_id):
        return []

    async def find_by_ids(self, user_ids):
        return []

    async def find_by_match(self, match_id):
        return []

    async def find_by_modality(self, modality_id):
        return next(iter(self._values.values()), None)


def _override_complete_match_state(match):
    team1_id, team2_id, bracket_id, modality_id = (uuid4() for _ in range(4))
    match.team1_id = team1_id
    match.team2_id = team2_id
    match.bracket_id = bracket_id
    match.match_type = MatchType.REGULAR
    match.match_category = MatchCategory.GROUP
    match.status = MatchStatus.IN_PROGRESS
    match.team1_score = 0
    match.team2_score = 0
    match.clock_seconds = 0
    match.clock_running = False
    match.current_period = 1

    app.dependency_overrides[get_team_repository] = lambda: _FakeStateRepository(
        {
            team1_id: Team(id=team1_id, name="Time A"),
            team2_id: Team(id=team2_id, name="Time B"),
        }
    )
    app.dependency_overrides[get_team_member_repository] = _FakeStateRepository
    app.dependency_overrides[get_user_repository] = _FakeStateRepository
    app.dependency_overrides[get_bracket_repository] = lambda: _FakeStateRepository(
        {bracket_id: Bracket(id=bracket_id, season_id=uuid4(), modality_id=modality_id)}
    )
    app.dependency_overrides[get_modality_repository] = lambda: _FakeStateRepository(
        {modality_id: Modality(id=modality_id, name="Futebol")}
    )
    app.dependency_overrides[
        get_modality_configuration_repository
    ] = lambda: _FakeStateRepository(
        {
            modality_id: ModalityConfiguration(
                id=uuid4(), modality_id=modality_id, score_type=ScoreType.GOALS
            )
        }
    )
    app.dependency_overrides[get_match_event_repository] = _FakeStateRepository
    app.dependency_overrides[get_match_set_repository] = _FakeStateRepository
    app.dependency_overrides[
        get_volleyball_modality_configuration_repository
    ] = _FakeStateRepository


class _ServerThread(threading.Thread):

    def __init__(self, port: int):
        super().__init__(daemon=True)
        self._config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        self._server = uvicorn.Server(self._config)

    def run(self):
        asyncio.run(self._server.serve())

    def stop(self):
        self._server.should_exit = True


@pytest.fixture(scope="module")
def live_server():
    port = 8765
    thread = _ServerThread(port)
    thread.start()
    for _ in range(50):
        if getattr(thread._server, "started", False):
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    thread.stop()
    thread.join(timeout=5)


@pytest.mark.integration
class TestRealtimeSSEFlow:
    async def test_ticket_then_sse_subscription_receives_published_event(
        self, live_server
    ):
        match_id = uuid4()
        user_id = uuid4()

        fake_match = Match(id=match_id, created_at=datetime.now())
        fake_user = User(id=user_id, role=UserRole.MONITOR, name="Monitor de Teste")

        app.dependency_overrides[get_match_repository] = lambda: _FakeMatchRepository(
            [fake_match]
        )
        _override_complete_match_state(fake_match)
        app.dependency_overrides[require_authenticated_user] = lambda: fake_user

        broadcaster = get_broadcaster_singleton()

        try:
            async with AsyncClient(base_url=live_server, timeout=10) as client:
                ticket_response = await client.post(
                    "/api/realtime/ticket",
                    json={"channel_type": "match", "channel_id": str(match_id)},
                )
                assert ticket_response.status_code == 200
                ticket = ticket_response.json()["data"]["ticket"]

                async def publish_soon():
                    await asyncio.sleep(0.3)
                    await broadcaster.publish(
                        f"match:{match_id}",
                        "goal_scored",
                        {"match_id": str(match_id), "team_id": "time-a"},
                    )

                publisher_task = asyncio.create_task(publish_soon())

                collected_lines: list[str] = []
                async with client.stream(
                    "GET", f"/api/match/{match_id}/live?ticket={ticket}"
                ) as stream_response:
                    assert stream_response.status_code == 200
                    async for line in stream_response.aiter_lines():
                        collected_lines.append(line)
                        if line.startswith("data:"):
                            break

                await publisher_task

            event_line = next(line for line in collected_lines if line.startswith("event:"))
            data_line = next(line for line in collected_lines if line.startswith("data:"))

            assert event_line.strip() == "event: goal_scored"
            payload = json.loads(data_line[len("data:"):].strip())
            assert payload["match_id"] == str(match_id)
            assert payload["team_id"] == "time-a"
        finally:
            app.dependency_overrides.clear()

    async def test_live_endpoint_rejects_ticket_issued_for_another_channel(
            self, live_server
    ):
        match_id = uuid4()
        other_match_id = uuid4()
        user_id = uuid4()

        fake_match = Match(id=match_id, created_at=datetime.now())
        other_fake_match = Match(id=other_match_id, created_at=datetime.now())
        other_fake_match.status = MatchStatus.IN_PROGRESS
        fake_user = User(id=user_id, role=UserRole.MONITOR, name="Monitor de Teste")

        app.dependency_overrides[get_match_repository] = lambda: _FakeMatchRepository(
            [fake_match, other_fake_match]
        )
        _override_complete_match_state(fake_match)
        app.dependency_overrides[require_authenticated_user] = lambda: fake_user

        try:
            async with AsyncClient(base_url=live_server, timeout=10) as client:
                ticket_response = await client.post(
                    "/api/realtime/ticket",
                    json={
                        "channel_type": "match",
                        "channel_id": str(other_match_id),
                    },
                )
                assert ticket_response.status_code == 200
                ticket = ticket_response.json()["data"]["ticket"]

                response = await client.get(
                    f"/api/match/{match_id}/live?ticket={ticket}"
                )
                assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    async def test_reconnects_sse_before_reconciling_current_match_state(
        self, live_server
    ):
        match_id = uuid4()
        user_id = uuid4()
        fake_match = Match(id=match_id, created_at=datetime.now())
        fake_user = User(id=user_id, role=UserRole.MONITOR, name="Monitor de Teste")

        app.dependency_overrides[get_match_repository] = lambda: _FakeMatchRepository(
            [fake_match]
        )
        _override_complete_match_state(fake_match)
        app.dependency_overrides[require_authenticated_user] = lambda: fake_user
        broadcaster = get_broadcaster_singleton()
        channel = f"match:{match_id}"

        try:
            async with AsyncClient(base_url=live_server, timeout=10) as client:
                ticket_response = await client.post(
                    "/api/realtime/ticket",
                    json={"channel_type": "match", "channel_id": str(match_id)},
                )
                first_ticket = ticket_response.json()["data"]["ticket"]

                async with client.stream(
                    "GET", f"/api/match/{match_id}/live?ticket={first_ticket}"
                ) as stream_response:
                    assert stream_response.status_code == 200
                    for _ in range(50):
                        if broadcaster.channel_subscriber_count(channel) == 1:
                            break
                        await asyncio.sleep(0.01)
                    assert broadcaster.channel_subscriber_count(channel) == 1

                ticket_response = await client.post(
                    "/api/realtime/ticket",
                    json={"channel_type": "match", "channel_id": str(match_id)},
                )
                second_ticket = ticket_response.json()["data"]["ticket"]

                async with client.stream(
                    "GET", f"/api/match/{match_id}/live?ticket={second_ticket}"
                ) as stream_response:
                    assert stream_response.status_code == 200
                    for _ in range(50):
                        if broadcaster.channel_subscriber_count(channel) == 1:
                            break
                        await asyncio.sleep(0.01)
                    assert broadcaster.channel_subscriber_count(channel) == 1

                    state_response = await client.get(f"/api/match/{match_id}")
                    assert state_response.status_code == 200
                    assert state_response.json()["data"]["match_id"] == str(match_id)

                    publish_task = asyncio.create_task(
                        broadcaster.publish(
                            channel,
                            "match_updated",
                            {"match_id": str(match_id), "status": "IN_PROGRESS"},
                        )
                    )
                    lines = []
                    async for line in stream_response.aiter_lines():
                        lines.append(line)
                        if line.startswith("data:"):
                            break
                    await publish_task

            assert "event: match_updated" in lines
        finally:
            app.dependency_overrides.clear()

    async def test_event_published_during_reconciliation_get_is_received_by_sse(
        self, live_server
    ):
        match_id = uuid4()
        user_id = uuid4()
        fake_match = Match(
            id=match_id,
            created_at=datetime.now(),
            metadata_json={"last_event": 40},
        )
        fake_user = User(id=user_id, role=UserRole.MONITOR, name="Monitor de Teste")
        broadcaster = get_broadcaster_singleton()
        channel = f"match:{match_id}"

        async def publish_event_41():
            await broadcaster.publish(
                channel,
                "match_updated",
                {"match_id": str(match_id), "sequence": 41},
            )

        repository = _PublishingMatchRepository([fake_match], publish_event_41)
        app.dependency_overrides[get_match_repository] = (
            lambda: repository
        )
        _override_complete_match_state(fake_match)
        app.dependency_overrides[require_authenticated_user] = lambda: fake_user

        try:
            async with AsyncClient(base_url=live_server, timeout=10) as client:
                ticket_response = await client.post(
                    "/api/realtime/ticket",
                    json={"channel_type": "match", "channel_id": str(match_id)},
                )
                ticket = ticket_response.json()["data"]["ticket"]

                async with client.stream(
                    "GET", f"/api/match/{match_id}/live?ticket={ticket}"
                ) as stream_response:
                    assert stream_response.status_code == 200
                    for _ in range(50):
                        if broadcaster.channel_subscriber_count(channel) == 1:
                            break
                        await asyncio.sleep(0.01)
                    assert broadcaster.channel_subscriber_count(channel) == 1

                    state_response = await client.get(f"/api/match/{match_id}")
                    assert state_response.status_code == 200
                    state = state_response.json()["data"]
                    assert state["metadata"]["last_event"] == 40

                    lines = []
                    async for line in stream_response.aiter_lines():
                        lines.append(line)
                        if line.startswith("data:"):
                            break

            event_line = next(line for line in lines if line.startswith("event:"))
            data_line = next(line for line in lines if line.startswith("data:"))
            assert event_line == "event: match_updated"
            assert json.loads(data_line[5:].strip())["sequence"] == 41
        finally:
            app.dependency_overrides.clear()
