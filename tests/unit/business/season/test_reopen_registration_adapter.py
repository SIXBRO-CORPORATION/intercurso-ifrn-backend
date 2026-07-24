from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.reopen_registration_adapter import ReopenRegistrationAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.enums.audit_action import AuditAction
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


def make_adapter():
    season_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    adapter = ReopenRegistrationAdapter(season_repository, user_repository, audit_logger)
    return adapter, season_repository, user_repository, audit_logger


def make_context(season_id=None, new_end=None):
    context = Context()
    context.put_property("season_id", season_id if season_id is not None else uuid4())
    context.put_property("new_registration_end_date", new_end)
    context.put_property("reopened_by", uuid4())
    return context


@pytest.mark.unit
class TestReopenRegistrationAdapter:
    async def test_reopens_closed_season(self):
        adapter, season_repository, user_repository, audit_logger = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.REGISTRATION_CLOSED,
            registration_start_date=now - timedelta(days=10),
            registration_closed_at=now - timedelta(days=1),
        )
        season_repository.get.return_value = season
        season_repository.save.return_value = season

        new_end = now + timedelta(days=10)
        result = await adapter.execute(make_context(season.id, new_end))

        assert result.status == SeasonStatus.REGISTRATION_OPEN
        assert result.registration_end_date == new_end
        assert result.registration_closed_at is None
        season_repository.save.assert_awaited_once()
        audit_logger.log.assert_awaited_once()
        assert (
            audit_logger.log.await_args.kwargs["action"]
            == AuditAction.SEASON_REGISTRATION_REOPENED
        )

    async def test_blocks_reopening_draft_season(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.DRAFT)
        season_repository.get.return_value = season

        context = make_context(
            season.id, datetime.now(timezone.utc) + timedelta(days=10)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_reopening_finished_season(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.FINISHED)
        season_repository.get.return_value = season

        context = make_context(
            season.id, datetime.now(timezone.utc) + timedelta(days=10)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_without_new_end_date(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.REGISTRATION_CLOSED)
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(season.id))

    async def test_blocks_new_end_date_in_the_past(self):
        adapter, season_repository, *_rest = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.REGISTRATION_CLOSED)
        season_repository.get.return_value = season

        context = make_context(
            season.id, datetime.now(timezone.utc) - timedelta(days=1)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_new_end_date_before_start_date(self):
        adapter, season_repository, *_rest = make_adapter()
        now = datetime.now(timezone.utc)
        season = Season(
            id=uuid4(),
            name="X",
            status=SeasonStatus.REGISTRATION_CLOSED,
            registration_start_date=now + timedelta(days=5),
        )
        season_repository.get.return_value = season

        context = make_context(season.id, now + timedelta(days=3))

        # ainda maior que agora, mas menor que a abertura futura
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_season_not_found(self):
        adapter, season_repository, *_rest = make_adapter()
        season_repository.get.return_value = None

        context = make_context(new_end=datetime.now(timezone.utc) + timedelta(days=10))

        with pytest.raises(BusinessException):
            await adapter.execute(context)