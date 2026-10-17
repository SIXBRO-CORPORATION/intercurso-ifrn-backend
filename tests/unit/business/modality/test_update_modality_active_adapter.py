from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.modality.update_modality_active_adapter import (
    UpdateModalityActiveAdapter,
)
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.not_found_exception import NotFoundException
from domain.modality.modality import Modality


def make_adapter():
    modality_repository = AsyncMock()
    audit_logger = AsyncMock()

    adapter = UpdateModalityActiveAdapter(modality_repository, audit_logger)

    return adapter, modality_repository, audit_logger


def make_context(modality_id=None, active=True, updated_by=None):
    context = Context()
    context.put_property("modality_id", modality_id if modality_id else uuid4())
    context.put_property("active", active)
    context.put_property("updated_by", updated_by if updated_by else uuid4())
    return context


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
async def test_deactivate_modality_saves_and_logs_audit():
    adapter, modality_repository, audit_logger = make_adapter()

    modality_id = uuid4()
    modality = make_modality(id=modality_id, active=True)
    modality_repository.get.return_value = modality
    modality_repository.save.return_value = make_modality(id=modality_id, active=False)

    context = make_context(modality_id=modality_id, active=False)
    result = await adapter.execute(context)

    modality_repository.get.assert_awaited_once_with(modality_id)
    saved_modality = modality_repository.save.await_args.args[0]
    assert saved_modality.active is False

    audit_logger.log.assert_awaited_once()
    _, kwargs = audit_logger.log.await_args
    assert kwargs["action"] == AuditAction.MODALITY_DEACTIVATED

    assert result.active is False


@pytest.mark.asyncio
async def test_activate_modality_logs_activated_action():
    adapter, modality_repository, audit_logger = make_adapter()

    modality_id = uuid4()
    modality = make_modality(id=modality_id, active=False)
    modality_repository.get.return_value = modality
    modality_repository.save.return_value = make_modality(id=modality_id, active=True)

    context = make_context(modality_id=modality_id, active=True)
    result = await adapter.execute(context)

    _, kwargs = audit_logger.log.await_args
    assert kwargs["action"] == AuditAction.MODALITY_ACTIVATED
    assert result.active is True


@pytest.mark.asyncio
async def test_update_modality_active_raises_not_found_when_missing():
    adapter, modality_repository, audit_logger = make_adapter()

    modality_repository.get.return_value = None

    context = make_context()

    with pytest.raises(NotFoundException):
        await adapter.execute(context)

    modality_repository.save.assert_not_called()
    audit_logger.log.assert_not_called()


@pytest.mark.asyncio
async def test_update_modality_active_is_idempotent_when_state_unchanged():
    adapter, modality_repository, audit_logger = make_adapter()

    modality_id = uuid4()
    modality = make_modality(id=modality_id, active=True)
    modality_repository.get.return_value = modality

    context = make_context(modality_id=modality_id, active=True)
    result = await adapter.execute(context)

    modality_repository.save.assert_not_called()
    audit_logger.log.assert_not_called()
    assert result is modality


@pytest.mark.asyncio
async def test_update_modality_active_requires_active_field():
    adapter, modality_repository, audit_logger = make_adapter()

    context = Context()
    context.put_property("modality_id", uuid4())
    context.put_property("updated_by", uuid4())

    with pytest.raises(BusinessException):
        await adapter.execute(context)

    modality_repository.get.assert_not_called()
