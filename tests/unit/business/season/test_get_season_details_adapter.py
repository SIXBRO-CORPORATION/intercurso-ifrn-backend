from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.get_season_details_adapter import GetSeasonDetailsAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season
from domain.season_modality import SeasonModality
from domain.team import Team


def make_adapter():
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()
    team_repository = AsyncMock()
    adapter = GetSeasonDetailsAdapter(
        season_repository, season_modality_repository, team_repository
    )
    return adapter, season_repository, season_modality_repository, team_repository


def make_context(season_id=None):
    context = Context()
    context.put_property("season_id", season_id if season_id is not None else uuid4())
    return context


@pytest.mark.unit
class TestGetSeasonDetailsAdapter:
    async def test_returns_season_with_modalities_and_stats(self):
        adapter, season_repository, season_modality_repository, team_repository = (
            make_adapter()
        )
        season = Season(id=uuid4(), name="Intercurso 2026", status=SeasonStatus.DRAFT)
        season_repository.get.return_value = season
        season_modality_repository.find_by_season.return_value = [
            SeasonModality(id=uuid4(), modality_id=uuid4())
        ]
        team_repository.find_by_season_id.return_value = [
            Team(id=uuid4(), status=TeamStatus.DRAFT),
            Team(id=uuid4(), status=TeamStatus.SUBMITTED),
            Team(id=uuid4(), status=TeamStatus.APPROVED),
            Team(id=uuid4(), status=TeamStatus.REJECTED),
        ]

        context = make_context(season.id)
        result = await adapter.execute(context)

        assert result is season
        assert context.get_property("total_teams_created", int) == 4
        assert context.get_property("total_teams_submitted", int) == 3
        assert context.get_property("total_teams_approved", int) == 1
        assert len(context.get_property("season_modalities", list)) == 1

    async def test_blocks_when_season_not_found(self):
        adapter, season_repository, *_ = make_adapter()
        season_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())

    async def test_blocks_when_season_id_missing(self):
        adapter, *_ = make_adapter()

        with pytest.raises(BusinessException):
            await adapter.execute(Context())
