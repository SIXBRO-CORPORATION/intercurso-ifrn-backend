from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.create_modality_adapter import CreateModalityAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


def make_adapter():
    modality_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    adapter = CreateModalityAdapter(
        modality_repository,
        modality_configuration_repository,
        user_repository,
        audit_logger,
    )
    return (
        adapter,
        modality_repository,
        modality_configuration_repository,
        user_repository,
        audit_logger,
    )


def make_context(
    name="Futsal",
    min_members=5,
    max_members=10,
    configuration=None,
    created_by=None,
):
    context = Context(data=Modality(name=name, min_members=min_members, max_members=max_members))
    if configuration is not None:
        context.put_property("modality_configuration", configuration)
    context.put_property("created_by", created_by if created_by is not None else uuid4())
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
            user_repository,
            audit_logger,
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

        audit_logger.log.assert_awaited_once()
        audit_call_kwargs = audit_logger.log.await_args.kwargs
        assert audit_call_kwargs["action"] == AuditAction.MODALITY_CREATED

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