from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.list_seasons_adapter import ListSeasonsAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.season.season import Season


def make_adapter():
    season_repository = AsyncMock()
    adapter = ListSeasonsAdapter(season_repository)
    return adapter, season_repository


@pytest.mark.unit
class TestListSeasonsAdapter:
    async def test_returns_all_seasons_when_no_filter(self):
        adapter, season_repository = make_adapter()
        seasons = [Season(id=uuid4(), name="Intercurso 2026")]
        season_repository.find_all.return_value = seasons

        result = await adapter.execute(Context())

        assert result == seasons
        season_repository.find_all.assert_awaited_once()
        season_repository.find_by_status.assert_not_called()
        season_repository.find_by_year.assert_not_called()

    async def test_filters_by_status_when_informed(self):
        adapter, season_repository = make_adapter()
        seasons = [Season(id=uuid4(), name="Intercurso 2026")]
        season_repository.find_by_status.return_value = seasons

        context = Context()
        context.put_property("status", SeasonStatus.REGISTRATION_OPEN)

        result = await adapter.execute(context)

        assert result == seasons
        season_repository.find_by_status.assert_awaited_once_with(
            SeasonStatus.REGISTRATION_OPEN
        )
        season_repository.find_all.assert_not_called()

    async def test_filters_by_year_when_status_not_informed(self):
        adapter, season_repository = make_adapter()
        seasons = [Season(id=uuid4(), name="Intercurso 2026")]
        season_repository.find_by_year.return_value = seasons

        context = Context()
        context.put_property("year", 2026)

        result = await adapter.execute(context)

        assert result == seasons
        season_repository.find_by_year.assert_awaited_once_with(2026)
        season_repository.find_all.assert_not_called()

    async def test_status_filter_takes_precedence_over_year(self):
        adapter, season_repository = make_adapter()
        season_repository.find_by_status.return_value = []

        context = Context()
        context.put_property("status", SeasonStatus.DRAFT)
        context.put_property("year", 2026)

        await adapter.execute(context)

        season_repository.find_by_status.assert_awaited_once_with(SeasonStatus.DRAFT)
        season_repository.find_by_year.assert_not_called()
