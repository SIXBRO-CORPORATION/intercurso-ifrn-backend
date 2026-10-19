import json
from uuid import uuid4

import pytest

from core.realtime import sse
from core.realtime.broadcaster import Broadcaster


class _FakeRequest:
    async def is_disconnected(self) -> bool:
        return False


def _parse(chunk: str) -> tuple[str, dict]:
    lines = chunk.strip().split("\n")
    event = next(line for line in lines if line.startswith("event:"))
    data = next(line for line in lines if line.startswith("data:"))
    return event[len("event:"):].strip(), json.loads(data[len("data:"):].strip())


@pytest.mark.unit
class TestStreamChannel:
    async def test_connection_limit_emits_structured_error_event(self):
        broadcaster = Broadcaster(max_connections_per_ip=0)
        channel = Broadcaster.match_channel(uuid4())

        chunks = [
            chunk
            async for chunk in sse.stream_channel(
                _FakeRequest(), broadcaster, channel, "ip:1.1.1.1"
            )
        ]

        assert len(chunks) == 1
        event, payload = _parse(chunks[0])
        assert event == "error"
        assert payload["code"] == "connection_limit"
        assert payload["retry_after_seconds"] == sse.CONNECTION_LIMIT_RETRY_SECONDS
        assert payload["detail"]

    async def test_idle_stream_emits_named_heartbeat_event(self, monkeypatch):
        monkeypatch.setattr(sse, "HEARTBEAT_INTERVAL_SECONDS", 0.01)
        broadcaster = Broadcaster()
        channel = Broadcaster.match_channel(uuid4())

        stream = sse.stream_channel(_FakeRequest(), broadcaster, channel, "ip:1.1.1.1")
        chunk = await anext(stream)
        await stream.aclose()

        assert _parse(chunk) == (sse.HEARTBEAT_EVENT, {})
        assert broadcaster.channel_subscriber_count(channel) == 0
