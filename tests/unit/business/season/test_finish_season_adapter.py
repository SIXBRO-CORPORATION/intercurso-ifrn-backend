from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.finish_season_adapter import FinishSeasonAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season
from domain.team import Team


def make_adapter():
    season_repository = AsyncMock()
    team_repository = AsyncMock()
    adapter = FinishSeasonAdapter(season_repository, team_repository)
    return adapter, season_repository, team_repository


def make_context(season_id=None, confirmation_name="Intercurso 2026"):
    context = Context()
    context.put_property("season_id", season_id if season_id is not None else uuid4())
    context.put_property("confirmation_name", confirmation_name)
    context.put_property("finished_by", uuid4())
    return context


@pytest.mark.unit
class TestFinishSeasonAdapter:
    async def test_finishes_in_progress_season_and_deactivates_invites(self):
        adapter, season_repository, team_repository = make_adapter()
        season = Season(
            id=uuid4(),
            name="Intercurso 2026",
            status=SeasonStatus.IN_PROGRESS,
            active=True,
        )
        team_one = Team(id=uuid4(), season_id=season.id, token_active=True)
        team_two = Team(id=uuid4(), season_id=season.id, token_active=False)

        season_repository.get.return_value = season
        season_repository.save.return_value = season
        team_repository.find_by_season_id.return_value = [team_one, team_two]

        result = await adapter.execute(
            make_context(season.id, confirmation_name="Intercurso 2026")
        )

        assert result.status == SeasonStatus.FINISHED
        assert result.finished_at is not None
        assert result.active is False
        season_repository.save.assert_awaited_once()

        # Apenas o time com convite ativo deve ser salvo novamente.
        team_repository.save.assert_awaited_once()
        assert team_one.token_active is False

    async def test_blocks_when_confirmation_name_does_not_match(self):
        adapter, season_repository, team_repository = make_adapter()
        season = Season(
            id=uuid4(), name="Intercurso 2026", status=SeasonStatus.IN_PROGRESS
        )
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(
                make_context(season.id, confirmation_name="Nome Errado")
            )

        season_repository.save.assert_not_awaited()
        team_repository.find_by_season_id.assert_not_awaited()

    async def test_blocks_when_confirmation_name_differs_only_by_case(self):
        adapter, season_repository, team_repository = make_adapter()
        season = Season(
            id=uuid4(), name="Intercurso 2026", status=SeasonStatus.IN_PROGRESS
        )
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(
                make_context(season.id, confirmation_name="intercurso 2026")
            )

    async def test_blocks_finishing_season_not_in_progress(self):
        adapter, season_repository, team_repository = make_adapter()
        season = Season(
            id=uuid4(), name="Intercurso 2026", status=SeasonStatus.DRAFT
        )
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(
                make_context(season.id, confirmation_name="Intercurso 2026")
            )

        season_repository.save.assert_not_awaited()

    async def test_blocks_when_season_not_found(self):
        adapter, season_repository, team_repository = make_adapter()
        season_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())

    async def test_blocks_when_confirmation_name_is_missing(self):
        adapter, season_repository, team_repository = make_adapter()

        context = Context()
        context.put_property("season_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        season_repository.get.assert_not_awaited()
