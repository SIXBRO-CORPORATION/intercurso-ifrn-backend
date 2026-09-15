from uuid import uuid4

import pytest

from core.realtime.broadcaster import Broadcaster
from core.realtime.live_ticket_port import InvalidLiveTicketError
from security.adapters.live_ticket_adapter import LiveTicketAdapter


@pytest.mark.unit
class TestLiveTicketAdapter:
    def test_issue_and_verify_round_trip(self):
        adapter = LiveTicketAdapter()
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        ticket = adapter.issue_ticket(user_id, channel)
        verified_user_id = adapter.verify_ticket(ticket, channel)

        assert verified_user_id == user_id

    def test_ticket_is_rejected_for_a_different_channel(self):
        adapter = LiveTicketAdapter()
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())
        other_channel = Broadcaster.match_channel(uuid4())

        ticket = adapter.issue_ticket(user_id, channel)

        with pytest.raises(InvalidLiveTicketError):
            adapter.verify_ticket(ticket, other_channel)

    def test_expired_ticket_is_rejected(self):
        adapter = LiveTicketAdapter(ttl_seconds=-1)
        user_id = uuid4()
        channel = Broadcaster.match_channel(uuid4())

        ticket = adapter.issue_ticket(user_id, channel)

        with pytest.raises(InvalidLiveTicketError):
            adapter.verify_ticket(ticket, channel)

    def test_garbage_string_is_rejected(self):
        adapter = LiveTicketAdapter()
        channel = Broadcaster.match_channel(uuid4())

        with pytest.raises(InvalidLiveTicketError):
            adapter.verify_ticket("not-a-jwt", channel)
