from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.close_registration_adapter import CloseRegistrationAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season


def make_adapter():
    season_repository = AsyncMock()
    adapter = CloseRegistrationAdapter(season_repository)
    return adapter, season_repository


def make_context(season_id=None):
    context = Context()
    context.put_property("season_id", season_id if season_id is not None else uuid4())
    context.put_property("closed_by", uuid4())
    return context


@pytest.mark.unit
class TestCloseRegistrationAdapter:
    async def test_closes_registration_open_season(self):
        adapter, season_repository = make_adapter()
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.REGISTRATION_OPEN,
            registration_end_date=datetime.now(timezone.utc) + timedelta(days=5),
        )
        season_repository.get.return_value = season
        season_repository.save.return_value = season

        result = await adapter.execute(make_context(season.id))

        assert result.status == SeasonStatus.REGISTRATION_CLOSED
        assert result.registration_closed_at is not None
        season_repository.save.assert_awaited_once()

    async def test_blocks_closing_draft_season(self):
        adapter, season_repository = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.DRAFT)
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(season.id))

    async def test_blocks_closing_already_closed_season(self):
        adapter, season_repository = make_adapter()
        season = Season(id=uuid4(), name="X", status=SeasonStatus.REGISTRATION_CLOSED)
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(season.id))

    async def test_blocks_when_season_not_found(self):
        adapter, season_repository = make_adapter()
        season_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())
