from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.get_bracket_config_suggestion_adapter import (
    GetBracketConfigSuggestionAdapter,
)
from core.context import Context
from domain.enums.modality_format import ModalityFormat
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


def make_adapter():
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()
    team_repository = AsyncMock()
    bracket_repository = AsyncMock()
    adapter = GetBracketConfigSuggestionAdapter(
        season_repository,
        season_modality_repository,
        team_repository,
        bracket_repository,
    )
    return (
        adapter,
        season_repository,
        season_modality_repository,
        team_repository,
        bracket_repository,
    )


class TestGetBracketConfigSuggestionAdapter:
    @pytest.mark.asyncio
    async def test_counts_approved_teams_without_loading_them(self):
        (
            adapter,
            season_repository,
            season_modality_repository,
            team_repository,
            bracket_repository,
        ) = make_adapter()
        season = Season(id=uuid4(), status=SeasonStatus.REGISTRATION_CLOSED)
        modality_id = uuid4()
        season_repository.find_active_season.return_value = season
        season_modality_repository.exists_by_season_and_modality.return_value = True
        bracket_repository.exists_active_bracket_for_modality.return_value = False
        team_repository.count_approved_teams_by_season_and_modality.return_value = 5

        context = Context()
        context.put_property("modality_id", modality_id)
        context.put_property("format", ModalityFormat.KNOCKOUT)

        configuration = await adapter.execute(context)

        team_repository.count_approved_teams_by_season_and_modality.assert_awaited_once_with(
            season.id, modality_id
        )
        team_repository.find_approved_teams_by_season_and_modality.assert_not_called()
        assert context.get_property("team_count", int) == 5
        # 5 times em mata-mata => chave de 8 => 3 byes.
        assert context.get_property("byes_estimated", int) == 3
        assert configuration is not None

    @pytest.mark.asyncio
    async def test_blocks_without_active_season(self):
        adapter, season_repository, *_ = make_adapter()
        season_repository.find_active_season.return_value = None

        context = Context()
        context.put_property("modality_id", uuid4())
        context.put_property("format", ModalityFormat.KNOCKOUT)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
