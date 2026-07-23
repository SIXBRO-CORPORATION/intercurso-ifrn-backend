from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from business.match.pause_clock_adapter import PauseClockAdapter
from business.match.resume_clock_adapter import ResumeClockAdapter
from core.context import Context
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


class TestPauseClockAdapter:
    @pytest.mark.asyncio
    async def test_pause_snapshots_elapsed_time(self):
        mocks = make_mocks()
        adapter = make_adapter(PauseClockAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        modified_at = datetime.now() - timedelta(seconds=30)
        match = make_in_progress_match(
            monitor_id=monitor_id,
            clock_seconds=100,
            clock_running=True,
            modified_at=modified_at,
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.clock_running is False
        # ~100 + 30s decorridos (com folga por causa do tempo de execução do teste)
        assert result.clock_seconds >= 129

    @pytest.mark.asyncio
    async def test_pause_already_paused_clock_raises(self):
        mocks = make_mocks()
        adapter = make_adapter(PauseClockAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id, clock_running=False)
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)


class TestResumeClockAdapter:
    @pytest.mark.asyncio
    async def test_resume_sets_clock_running_true(self):
        mocks = make_mocks()
        adapter = make_adapter(ResumeClockAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(
            monitor_id=monitor_id, clock_seconds=250, clock_running=False
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.clock_running is True
        assert result.clock_seconds == 250

    @pytest.mark.asyncio
    async def test_resume_already_running_clock_raises(self):
        mocks = make_mocks()
        adapter = make_adapter(ResumeClockAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id, clock_running=True)
        mocks["match_repository"].get.return_value = match

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
