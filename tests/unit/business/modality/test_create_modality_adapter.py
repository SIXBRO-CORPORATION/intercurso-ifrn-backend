from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.create_modality_adapter import CreateModalityAdapter
from core.context import Context
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)


def make_adapter():
    modality_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()
    volleyball_modality_configuration_repository = AsyncMock()
    adapter = CreateModalityAdapter(
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


def make_context(
    name="Futsal",
    min_members=5,
    max_members=10,
    configuration=None,
):
    context = Context(data=Modality(name=name, min_members=min_members, max_members=max_members))
    if configuration is not None:
        context.put_property("modality_configuration", configuration)
    return context


def make_valid_configuration(**overrides):
    defaults = dict(
        num_periods=2,
        period_durations_minutes=20,
        score_type=ScoreType.GOALS,
        has_third_place_match=True,
    )
    defaults.update(overrides)
    return ModalityConfiguration(**defaults)


@pytest.mark.unit
class TestCreateModalityAdapter:
    async def test_creates_modality_and_configuration_successfully(self):
        (
            adapter,
            modality_repository,
            modality_configuration_repository,
            _volleyball_modality_configuration_repository,
        ) = make_adapter()
        modality_repository.find_by_name.return_value = None
        saved_modality_id = uuid4()
        modality_repository.save.return_value = Modality(
            id=saved_modality_id,
            name="Futsal",
            min_members=5,
            max_members=10,
            active=True,
        )
        modality_configuration_repository.save.side_effect = lambda config: config

        context = make_context(configuration=make_valid_configuration())

        result = await adapter.execute(context)

        assert result.name == "Futsal"
        assert result.active is True
        modality_repository.save.assert_awaited_once()

        saved_configuration_arg = (
            modality_configuration_repository.save.await_args.args[0]
        )
        assert saved_configuration_arg.modality_id == saved_modality_id
        assert saved_configuration_arg.num_periods == 2
        assert saved_configuration_arg.score_type == ScoreType.GOALS

        assert context.get_property(
            "modality_configuration", ModalityConfiguration
        ).modality_id == saved_modality_id

    async def test_blocks_empty_name(self):
        adapter, *_ = make_adapter()
        context = make_context(
            name="   ", configuration=make_valid_configuration()
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_min_members_below_one(self):
        adapter, *_ = make_adapter()
        context = make_context(
            name="Vôlei",
            min_members=0,
            max_members=5,
            configuration=make_valid_configuration(),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_max_members_below_min_members(self):
        adapter, *_ = make_adapter()
        context = make_context(
            name="Vôlei",
            min_members=6,
            max_members=5,
            configuration=make_valid_configuration(),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_duplicated_name(self):
        adapter, modality_repository, *_ = make_adapter()
        modality_repository.find_by_name.return_value = Modality(
            id=uuid4(), name="Futsal", min_members=5, max_members=10
        )

        context = make_context(configuration=make_valid_configuration())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_data(self):
        adapter, *_ = make_adapter()
        context = Context()

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_configuration(self):
        adapter, *_ = make_adapter()
        context = make_context(configuration=None)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_num_periods_below_one(self):
        adapter, *_ = make_adapter()
        context = make_context(
            configuration=make_valid_configuration(num_periods=0)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_period_duration_below_one(self):
        adapter, *_ = make_adapter()
        context = make_context(
            configuration=make_valid_configuration(period_durations_minutes=0)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_score_type(self):
        adapter, *_ = make_adapter()
        context = make_context(
            configuration=make_valid_configuration(score_type=None)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_volleyball_configuration_for_sets(self):
        adapter, modality_repository, *_ = make_adapter()
        modality_repository.find_by_name.return_value = None

        context = make_context(
            name="Vôlei", configuration=make_valid_configuration(score_type=ScoreType.SETS)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_points_per_set_below_one(self):
        adapter, modality_repository, *_ = make_adapter()
        modality_repository.find_by_name.return_value = None

        context = make_context(
            name="Vôlei", configuration=make_valid_configuration(score_type=ScoreType.SETS)
        )
        context.put_property(
            "volleyball_configuration",
            VolleyballModalityConfiguration(
                points_per_set=0, final_set_points=15, sets_to_win=2
            ),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_final_set_points_below_one(self):
        adapter, modality_repository, *_ = make_adapter()
        modality_repository.find_by_name.return_value = None

        context = make_context(
            name="Vôlei", configuration=make_valid_configuration(score_type=ScoreType.SETS)
        )
        context.put_property(
            "volleyball_configuration",
            VolleyballModalityConfiguration(
                points_per_set=25, final_set_points=0, sets_to_win=2
            ),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_sets_to_win_below_one(self):
        adapter, modality_repository, *_ = make_adapter()
        modality_repository.find_by_name.return_value = None

        context = make_context(
            name="Vôlei", configuration=make_valid_configuration(score_type=ScoreType.SETS)
        )
        context.put_property(
            "volleyball_configuration",
            VolleyballModalityConfiguration(
                points_per_set=25, final_set_points=15, sets_to_win=0
            ),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_creates_volleyball_configuration_when_score_type_is_sets(self):
        (
            adapter,
            modality_repository,
            modality_configuration_repository,
            volleyball_modality_configuration_repository,
        ) = make_adapter()
        modality_repository.find_by_name.return_value = None
        saved_modality_id = uuid4()
        modality_repository.save.return_value = Modality(
            id=saved_modality_id,
            name="Vôlei",
            min_members=6,
            max_members=12,
            active=True,
        )
        saved_configuration_id = uuid4()

        def save_configuration(config):
            config.id = saved_configuration_id
            return config

        modality_configuration_repository.save.side_effect = save_configuration
        volleyball_modality_configuration_repository.save.side_effect = (
            lambda config: config
        )

        context = make_context(
            name="Vôlei",
            min_members=6,
            max_members=12,
            configuration=make_valid_configuration(score_type=ScoreType.SETS),
        )
        context.put_property(
            "volleyball_configuration",
            VolleyballModalityConfiguration(
                points_per_set=25, final_set_points=15, sets_to_win=2
            ),
        )

        result = await adapter.execute(context)

        assert result.name == "Vôlei"
        volleyball_modality_configuration_repository.save.assert_awaited_once()
        saved_volleyball_arg = (
            volleyball_modality_configuration_repository.save.await_args.args[0]
        )
        assert (
            saved_volleyball_arg.modality_configuration_id == saved_configuration_id
        )
        assert saved_volleyball_arg.points_per_set == 25
        assert saved_volleyball_arg.final_set_points == 15
        assert saved_volleyball_arg.sets_to_win == 2

        assert (
            context.get_property(
                "volleyball_configuration", VolleyballModalityConfiguration
            ).modality_configuration_id
            == saved_configuration_id
        )
