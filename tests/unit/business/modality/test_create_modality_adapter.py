from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.create_modality_adapter import CreateModalityAdapter
from core.context import Context
from domain.exceptions.business_exception import BusinessException
from domain.modality import Modality


def make_adapter():
    modality_repository = AsyncMock()
    adapter = CreateModalityAdapter(modality_repository)
    return adapter, modality_repository


@pytest.mark.unit
class TestCreateModalityAdapter:
    async def test_creates_modality_successfully(self):
        adapter, modality_repository = make_adapter()
        modality_repository.find_by_name.return_value = None
        modality_repository.save.return_value = Modality(
            id=uuid4(), name="Futsal", min_members=5, max_members=10, active=True
        )

        context = Context(
            data=Modality(name="Futsal", min_members=5, max_members=10)
        )

        result = await adapter.execute(context)

        assert result.name == "Futsal"
        assert result.active is True
        modality_repository.save.assert_awaited_once()

    async def test_blocks_empty_name(self):
        adapter, _ = make_adapter()
        context = Context(data=Modality(name="   ", min_members=1, max_members=5))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_min_members_below_one(self):
        adapter, _ = make_adapter()
        context = Context(
            data=Modality(name="Vôlei", min_members=0, max_members=5)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_max_members_below_min_members(self):
        adapter, _ = make_adapter()
        context = Context(
            data=Modality(name="Vôlei", min_members=6, max_members=5)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_duplicated_name(self):
        adapter, modality_repository = make_adapter()
        modality_repository.find_by_name.return_value = Modality(
            id=uuid4(), name="Futsal", min_members=5, max_members=10
        )

        context = Context(
            data=Modality(name="Futsal", min_members=5, max_members=10)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_data(self):
        adapter, _ = make_adapter()
        context = Context()

        with pytest.raises(BusinessException):
            await adapter.execute(context)
