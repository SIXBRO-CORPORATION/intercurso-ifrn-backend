from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.list_modalities_adapter import ListModalitiesAdapter
from core.context import Context
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


def make_adapter():
    modality_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()

    adapter = ListModalitiesAdapter(
        modality_repository, modality_configuration_repository
    )

    return adapter, modality_repository, modality_configuration_repository


def make_modality(**overrides):
    defaults = dict(
        id=uuid4(),
        name="Futsal",
        min_members=5,
        max_members=10,
        gender_mode=ModalityGenderMode.MIXED,
        active=True,
    )
    defaults.update(overrides)
    return Modality(**defaults)


@pytest.mark.asyncio
async def test_list_modalities_without_season_id_uses_find_active_modalities():
    adapter, modality_repository, configuration_repository = make_adapter()

    modality = make_modality()
    modality_repository.find_active_modalities.return_value = [modality]
    configuration = ModalityConfiguration(
        modality_id=modality.id,
        num_periods=2,
        period_durations_minutes=20,
        score_type=ScoreType.GOALS,
        has_third_place_match=True,
    )
    configuration_repository.find_by_modality_ids.return_value = [configuration]

    context = Context()
    result = await adapter.execute(context)

    modality_repository.find_active_modalities.assert_awaited_once()
    modality_repository.find_active_by_season.assert_not_called()
    configuration_repository.find_by_modality_ids.assert_awaited_once_with(
        [modality.id]
    )

    assert result == [modality]
    configurations = context.get_property("modality_configurations", dict)
    assert configurations[modality.id] == configuration


@pytest.mark.asyncio
async def test_list_modalities_with_season_id_uses_find_active_by_season():
    adapter, modality_repository, configuration_repository = make_adapter()

    season_id = uuid4()
    modality = make_modality()
    modality_repository.find_active_by_season.return_value = [modality]
    configuration_repository.find_by_modality_ids.return_value = []

    context = Context()
    context.put_property("season_id", season_id)

    result = await adapter.execute(context)

    modality_repository.find_active_by_season.assert_awaited_once_with(season_id)
    modality_repository.find_active_modalities.assert_not_called()
    assert result == [modality]
    assert context.get_property("modality_configurations", dict) == {}


@pytest.mark.asyncio
async def test_list_modalities_skips_configuration_lookup_when_empty():
    adapter, modality_repository, configuration_repository = make_adapter()

    modality_repository.find_active_modalities.return_value = []

    context = Context()
    result = await adapter.execute(context)

    assert result == []
    configuration_repository.find_by_modality_ids.assert_not_called()
    assert context.get_property("modality_configurations", dict) == {}
