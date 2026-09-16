from uuid import uuid4

import pytest
from jose import jwt

from core.realtime.broadcaster import Broadcaster
from core.realtime.live_ticket_port import InvalidLiveTicketError
from security.adapters.live_ticket_adapter import LiveTicketAdapter, TICKET_SCOPE_CLAIM
from security.config import settings


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

    def test_ticket_without_exp_is_rejected(self):
        adapter = LiveTicketAdapter()
        channel = Broadcaster.match_channel(uuid4())
        forged = jwt.encode(
            {"sub": str(uuid4()), "scope": TICKET_SCOPE_CLAIM, "channel": channel},
            settings.live_ticket_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(InvalidLiveTicketError):
            adapter.verify_ticket(forged, channel)