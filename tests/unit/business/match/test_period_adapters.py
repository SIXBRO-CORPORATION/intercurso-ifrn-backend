from uuid import uuid4

import pytest

from business.match.end_period_adapter import EndPeriodAdapter
from business.match.start_period_adapter import StartPeriodAdapter
from core.context import Context
from domain.enums.event_type import EventType
from domain.exceptions.business_exception import BusinessException

from tests.unit.business.match._helpers import (
    make_adapter,
    make_in_progress_match,
    make_mocks,
    stub_empty_management_context,
)


def make_context(match_id, monitor_id):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    return context


class TestEndPeriodAdapter:
    @pytest.mark.asyncio
    async def test_end_period_pauses_clock_and_increments_period(self):
        mocks = make_mocks()
        adapter = make_adapter(EndPeriodAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(
            monitor_id=monitor_id, current_period=1, clock_running=True
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.current_period == 2
        assert result.clock_running is False

        saved_event = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.PERIOD_END


class TestStartPeriodAdapter:
    @pytest.mark.asyncio
    async def test_start_period_resumes_clock(self):
        mocks = make_mocks()
        adapter = make_adapter(StartPeriodAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(
            monitor_id=monitor_id, current_period=2, clock_running=False
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.clock_running is True

        saved_event = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.PERIOD_START

    @pytest.mark.asyncio
    async def test_start_period_blocked_when_clock_still_running(self):
        mocks = make_mocks()
        adapter = make_adapter(StartPeriodAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id, clock_running=True)
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
