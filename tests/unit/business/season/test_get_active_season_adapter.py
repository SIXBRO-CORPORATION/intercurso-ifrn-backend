from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.get_active_season_adapter import GetActiveSeasonAdapter
from core.context import Context
from domain.exceptions.business_exception import BusinessException
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

    async def test_blocks_when_no_active_season(self):
        adapter, season_repository = make_adapter()
        season_repository.find_active_season.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(Context())
