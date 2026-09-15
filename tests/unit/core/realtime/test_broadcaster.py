import asyncio
from uuid import uuid4

import pytest

from core.realtime.broadcaster import (
    Broadcaster,
    ConnectionLimitExceededError,
)


@pytest.mark.unit
class TestBroadcaster:
    async def test_publish_delivers_to_subscribed_channel(self):
        broadcaster = Broadcaster()
        match_id = uuid4()
        user_id = uuid4()
        channel = Broadcaster.match_channel(match_id)

        queue = await broadcaster.subscribe(channel, user_id)
        await broadcaster.publish(channel, "goal_scored", {"team_id": "1"})

        event = queue.get_nowait()
        assert event.event_type == "goal_scored"
        assert event.payload == {"team_id": "1"}

    async def test_publish_does_not_leak_across_channels(self):
        broadcaster = Broadcaster()
        user_id = uuid4()
        channel_a = Broadcaster.match_channel(uuid4())
        channel_b = Broadcaster.match_channel(uuid4())

        queue_a = await broadcaster.subscribe(channel_a, user_id)
        await broadcaster.publish(channel_b, "goal_scored", {})

        assert queue_a.empty()

    async def test_unsubscribe_removes_queue_from_channel(self):
        broadcaster = Broadcaster()
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        queue = await broadcaster.subscribe(channel, user_id)
        assert broadcaster.channel_subscriber_count(channel) == 1

        await broadcaster.unsubscribe(channel, user_id, queue)
        assert broadcaster.channel_subscriber_count(channel) == 0

        await broadcaster.publish(channel, "goal_scored", {})

    async def test_queue_discards_oldest_when_full(self):
        broadcaster = Broadcaster(queue_max_size=2)
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        queue = await broadcaster.subscribe(channel, user_id)

        await broadcaster.publish(channel, "EVT", {"n": 1})
        await broadcaster.publish(channel, "EVT", {"n": 2})
        await broadcaster.publish(channel, "EVT", {"n": 3})

        assert queue.qsize() == 2
        first = queue.get_nowait()
        second = queue.get_nowait()
        assert [first.payload["n"], second.payload["n"]] == [2, 3]

    async def test_connection_limit_per_user_is_enforced(self):
        broadcaster = Broadcaster(max_connections_per_user=2)
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        await broadcaster.subscribe(channel, user_id)
        await broadcaster.subscribe(channel, user_id)

        with pytest.raises(ConnectionLimitExceededError):
            await broadcaster.subscribe(channel, user_id)

    async def test_slow_consumer_never_blocks_publish(self):
        broadcaster = Broadcaster(queue_max_size=1)
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        await broadcaster.subscribe(channel, user_id)

        async def publish_many():
            for i in range(50):
                await broadcaster.publish(channel, "EVT", {"n": i})

        await asyncio.wait_for(publish_many(), timeout=1)
