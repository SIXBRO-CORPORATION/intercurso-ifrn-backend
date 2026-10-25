from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.list_all_modalities_adapter import ListAllModalitiesAdapter
from core.context import Context
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)


def make_adapter(volleyball_modality_configuration_repository=None):
    modality_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()
    volleyball_modality_configuration_repository = (
        volleyball_modality_configuration_repository or AsyncMock()
    )

    adapter = ListAllModalitiesAdapter(
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
    )

    return (
        adapter,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
    )


@pytest.mark.asyncio
async def test_list_all_modalities_returns_active_and_inactive():
    adapter, modality_repository, configuration_repository, _ = make_adapter()

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


@pytest.mark.asyncio
async def test_list_all_modalities_attaches_volleyball_configuration_for_sets_modality():
    (
        adapter,
        modality_repository,
        configuration_repository,
        volleyball_repository,
    ) = make_adapter()

    goals_modality = Modality(
        id=uuid4(),
        name="Futsal",
        min_members=5,
        max_members=10,
        gender_mode=ModalityGenderMode.MIXED,
        active=True,
    )
    sets_modality = Modality(
        id=uuid4(),
        name="Voleibol Indoor",
        min_members=6,
        max_members=12,
        gender_mode=ModalityGenderMode.MIXED,
        active=True,
    )
    modality_repository.find_all.return_value = [goals_modality, sets_modality]

    goals_configuration = ModalityConfiguration(
        id=uuid4(),
        modality_id=goals_modality.id,
        num_periods=2,
        period_durations_minutes=20,
        score_type=ScoreType.GOALS,
    )
    sets_configuration = ModalityConfiguration(
        id=uuid4(),
        modality_id=sets_modality.id,
        num_periods=3,
        period_durations_minutes=0,
        score_type=ScoreType.SETS,
    )
    configuration_repository.find_by_modality_ids.return_value = [
        goals_configuration,
        sets_configuration,
    ]

    volleyball_configuration = VolleyballModalityConfiguration(
        modality_configuration_id=sets_configuration.id,
        points_per_set=25,
        final_set_points=15,
        sets_to_win=3,
    )
    volleyball_repository.find_by_modality_configuration_ids.return_value = [
        volleyball_configuration
    ]

    context = Context()
    await adapter.execute(context)

    # achado #1 do QA M03: só a modalidade com score_type=SETS é buscada/anexada.
    volleyball_repository.find_by_modality_configuration_ids.assert_awaited_once_with(
        [sets_configuration.id]
    )
    volleyball_configurations = context.get_property(
        "modality_volleyball_configurations", dict
    )
    assert goals_modality.id not in volleyball_configurations
    assert volleyball_configurations[sets_modality.id] == volleyball_configuration
