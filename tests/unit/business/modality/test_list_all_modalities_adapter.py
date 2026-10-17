from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.list_all_modalities_adapter import ListAllModalitiesAdapter
from core.context import Context
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


def make_adapter():
    modality_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()

    adapter = ListAllModalitiesAdapter(
        modality_repository, modality_configuration_repository
    )

    return adapter, modality_repository, modality_configuration_repository


@pytest.mark.asyncio
async def test_list_all_modalities_returns_active_and_inactive():
    adapter, modality_repository, configuration_repository = make_adapter()

    active_modality = Modality(
        id=uuid4(),
        name="Futsal",
        min_members=5,
        max_members=10,
        gender_mode=ModalityGenderMode.MIXED,
        active=True,
    )
    inactive_modality = Modality(
        id=uuid4(),
        name="Xadrez",
        min_members=1,
        max_members=1,
        gender_mode=ModalityGenderMode.MIXED,
        active=False,
    )
    modality_repository.find_all.return_value = [active_modality, inactive_modality]

    configuration = ModalityConfiguration(
        modality_id=active_modality.id,
        num_periods=2,
        period_durations_minutes=20,
        score_type=ScoreType.GOALS,
        has_third_place_match=True,
    )
    configuration_repository.find_by_modality_ids.return_value = [configuration]

    context = Context()
    result = await adapter.execute(context)

    modality_repository.find_all.assert_awaited_once()
    configuration_repository.find_by_modality_ids.assert_awaited_once_with(
        [active_modality.id, inactive_modality.id]
    )

    assert result == [active_modality, inactive_modality]
    configurations = context.get_property("modality_configurations", dict)
    assert configurations[active_modality.id] == configuration
    assert inactive_modality.id not in configurations
