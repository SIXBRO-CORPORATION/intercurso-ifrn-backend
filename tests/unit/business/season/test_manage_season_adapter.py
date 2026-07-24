from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.manage_season_adapter import ManageSeasonAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.enums.audit_action import AuditAction
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


def make_adapter():
    season_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    adapter = ManageSeasonAdapter(season_repository, user_repository, audit_logger)
    return adapter, season_repository, user_repository, audit_logger


def make_context(season_id=None, new_start=None, new_end=None, reason=None):
    context = Context()
    context.put_property("season_id", season_id if season_id is not None else uuid4())
    context.put_property("new_registration_start_date", new_start)
    context.put_property("new_registration_end_date", new_end)
    context.put_property("reason", reason)
    context.put_property("updated_by", uuid4())
    return context


@pytest.mark.unit
class TestManageSeasonAdapter:
    async def test_edits_both_dates_in_draft(self):
        adapter, season_repository, user_repository, audit_logger = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.DRAFT,
            registration_start_date=now + timedelta(days=5),
            registration_end_date=now + timedelta(days=10),
        )
        season_repository.get.return_value = season
        season_repository.save.return_value = season

        new_start = now + timedelta(days=2)
        new_end = now + timedelta(days=8)
        context = make_context(new_start=new_start, new_end=new_end)

        result = await adapter.execute(context)

        assert result.registration_start_date == new_start
        assert result.registration_end_date == new_end
        season_repository.save.assert_awaited_once()
        audit_logger.log.assert_awaited_once()
        assert (
            audit_logger.log.await_args.kwargs["action"]
            == AuditAction.SEASON_DATES_UPDATED
        )

    async def test_edits_only_end_date_in_registration_open(self):
        adapter, season_repository, *_rest = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.REGISTRATION_OPEN,
            registration_start_date=now - timedelta(days=1),
            registration_end_date=now + timedelta(days=10),
        )
        season_repository.get.return_value = season
        season_repository.save.return_value = season

        new_end = now + timedelta(days=20)
        context = make_context(new_end=new_end)

        result = await adapter.execute(context)

        assert result.registration_end_date == new_end
        season_repository.save.assert_awaited_once()

    async def test_blocks_editing_start_date_in_registration_open(self):
        adapter, season_repository, *_rest = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.REGISTRATION_OPEN,
            registration_start_date=now - timedelta(days=1),
            registration_end_date=now + timedelta(days=10),
        )
        season_repository.get.return_value = season

        context = make_context(new_start=now + timedelta(days=1))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_editing_in_progress_season(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.IN_PROGRESS)
        season_repository.get.return_value = season

        context = make_context(new_end=datetime.now(timezone.utc) + timedelta(days=10))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_editing_finished_season(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.FINISHED)
        season_repository.get.return_value = season

        context = make_context(new_end=datetime.now(timezone.utc) + timedelta(days=10))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_start_date_in_the_past(self):
        adapter, season_repository, *_rest = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="X",
            status=SeasonStatus.DRAFT,
            registration_start_date=now + timedelta(days=5),
            registration_end_date=now + timedelta(days=10),
        )
        season_repository.get.return_value = season

        context = make_context(new_start=now - timedelta(days=1))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_end_date_before_start_date(self):
        adapter, season_repository, *_rest = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="X",
            status=SeasonStatus.DRAFT,
            registration_start_date=now + timedelta(days=5),
            registration_end_date=now + timedelta(days=10),
        )
        season_repository.get.return_value = season

        context = make_context(new_end=now + timedelta(days=1))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_no_dates_informed(self):
        adapter, _, *_rest = make_adapter()
        context = make_context()

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_season_not_found(self):
        adapter, season_repository, *_rest = make_adapter()
        season_repository.get.return_value = None

        context = make_context(new_end=datetime.now(timezone.utc) + timedelta(days=10))

        with pytest.raises(BusinessException):
            await adapter.execute(context)