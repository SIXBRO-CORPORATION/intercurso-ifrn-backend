from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.get_active_season_adapter import GetActiveSeasonAdapter
from core.context import Context
from domain.exceptions.not_found_exception import NotFoundException
from domain.season.season import Season


def make_adapter():
    season_repository = AsyncMock()
    adapter = GetActiveSeasonAdapter(season_repository)
    return adapter, season_repository


@pytest.mark.unit
class TestGetActiveSeasonAdapter:
    async def test_returns_active_season(self):
        adapter, season_repository = make_adapter()
        season = Season(id=uuid4(), name="Intercurso 2026", active=True)
        season_repository.find_active_season.return_value = season

        result = await adapter.execute(Context())

        assert result is season

    async def test_falls_back_to_last_season_when_none_is_active(self):
        adapter, season_repository = make_adapter()
        last = Season(id=uuid4(), name="Intercurso 2025", active=False)
        season_repository.find_active_season.return_value = None
        season_repository.find_last_season.return_value = last

        result = await adapter.execute(Context())

        assert result is last

    async def test_active_season_takes_precedence_over_fallback(self):
        adapter, season_repository = make_adapter()
        season_repository.find_active_season.return_value = Season(
            id=uuid4(), name="Atual", active=True
        )

        await adapter.execute(Context())

        season_repository.find_last_season.assert_not_awaited()

    async def test_not_found_when_no_season_exists(self):
        adapter, season_repository = make_adapter()
        season_repository.find_active_season.return_value = None
        season_repository.find_last_season.return_value = None

        with pytest.raises(NotFoundException):
            await adapter.execute(Context())
