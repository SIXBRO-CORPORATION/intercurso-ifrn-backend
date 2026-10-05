from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.create_season_adapter import CreateSeasonAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.season.season_modality import SeasonModality


def make_adapter():
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()
    modality_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()

    adapter = CreateSeasonAdapter(
        season_repository,
        season_modality_repository,
        modality_repository,
        audit_logger,
    )
    return (
        adapter,
        season_repository,
        season_modality_repository,
        modality_repository,
        user_repository,
        audit_logger,
    )


def make_context(
        name="Intercurso 2026",
        year=None,
        modality_ids=None,
        registration_start_date=None,
        registration_end_date=None,
        open_immediately=False,
):
    now = datetime.now(timezone.utc)
    year = year if year is not None else now.year
    modality_ids = modality_ids if modality_ids is not None else [uuid4()]
    registration_start_date = (
        registration_start_date
        if registration_start_date is not None
        else now + timedelta(days=1)
    )
    registration_end_date = (
        registration_end_date
        if registration_end_date is not None
        else now + timedelta(days=10)
    )

    season = Season(
        name=name,
        year=year,
        registration_start_date=registration_start_date,
        registration_end_date=registration_end_date,
    )

    context = Context(data=season)
    context.put_property("modality_ids", modality_ids)
    context.put_property("open_immediately", open_immediately)
    context.put_property("created_by", uuid4())
    return context


@pytest.mark.unit
class TestCreateSeasonAdapter:
    async def test_creates_season_as_draft_successfully(self):
        (
            adapter,
            season_repository,
            season_modality_repository,
            modality_repository,
            user_repository,
            audit_logger,
        ) = make_adapter()
        modality_id = uuid4()
        modality_repository.find_by_ids.return_value = [
            Modality(
                id=modality_id, name="Futsal", min_members=5, max_members=10, active=True
            )
        ]
        season_repository.save.return_value = Season(
            id=uuid4(), name="Intercurso 2026", year=datetime.now(timezone.utc).year
        )
        season_modality_repository.save.return_value = SeasonModality(
            id=uuid4(), modality_id=modality_id
        )

        context = make_context(modality_ids=[modality_id])

        result = await adapter.execute(context)

        assert result is not None
        season_repository.save.assert_awaited_once()
        season_modality_repository.save.assert_awaited_once()
        # Abertura não imediata: não deve nem consultar temporada ativa
        season_repository.find_active_season.assert_not_awaited()
        audit_logger.log.assert_awaited_once()
        assert (
                audit_logger.log.await_args.kwargs["action"] == AuditAction.SEASON_CREATED
        )

    async def test_draft_season_is_created_inactive(self):
        (
            adapter,
            season_repository,
            season_modality_repository,
            modality_repository,
            user_repository,
            audit_logger,
        ) = make_adapter()
        modality_id = uuid4()
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal", min_members=5, max_members=10, active=True)
        ]
        season_repository.save.side_effect = lambda s: s
        season_modality_repository.save.return_value = SeasonModality(
            id=uuid4(), modality_id=modality_id
        )

        await adapter.execute(make_context(modality_ids=[modality_id]))

        saved = season_repository.save.await_args.args[0]
        assert saved.active is False
        assert saved.status == SeasonStatus.DRAFT

    async def test_open_immediately_is_blocked_when_another_season_is_active(self):
        (
            adapter,
            season_repository,
            season_modality_repository,
            modality_repository,
            user_repository,
            audit_logger,
        ) = make_adapter()
        modality_id = uuid4()
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal", min_members=5, max_members=10, active=True)
        ]
        season_repository.find_active_season.return_value = Season(
            id=uuid4(), name="Atual", active=True, status=SeasonStatus.IN_PROGRESS
        )

        with pytest.raises(BusinessException, match="Finalize a temporada atual"):
            await adapter.execute(
                make_context(
                    modality_ids=[modality_id],
                    registration_start_date=None,
                    open_immediately=True,
                )
            )

        season_repository.save.assert_not_awaited()

    async def test_open_immediately_creates_season_active_when_none_is_active(self):
        (
            adapter,
            season_repository,
            season_modality_repository,
            modality_repository,
            user_repository,
            audit_logger,
        ) = make_adapter()
        modality_id = uuid4()
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal", min_members=5, max_members=10, active=True)
        ]
        season_repository.find_active_season.return_value = None
        season_repository.save.side_effect = lambda s: s
        season_modality_repository.save.return_value = SeasonModality(
            id=uuid4(), modality_id=modality_id
        )

        await adapter.execute(
            make_context(
                modality_ids=[modality_id],
                registration_start_date=None,
                open_immediately=True,
            )
        )

        saved = season_repository.save.await_args.args[0]
        assert saved.active is True
        assert saved.status == SeasonStatus.REGISTRATION_OPEN
        season_repository.save.assert_awaited_once()

    async def test_blocks_empty_name(self):
        adapter, *_ = make_adapter()
        context = make_context(name="   ")

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_year_before_current(self):
        adapter, *_ = make_adapter()
        context = make_context(year=datetime.now(timezone.utc).year - 1)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_without_modalities(self):
        adapter, *_ = make_adapter()
        context = make_context(modality_ids=[])

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_start_date_in_the_past(self):
        adapter, *_ = make_adapter()
        context = make_context(
            registration_start_date=datetime.now(timezone.utc) - timedelta(days=1)
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_end_date_before_start_date(self):
        adapter, *_ = make_adapter()
        now = datetime.now(timezone.utc)
        context = make_context(
            registration_start_date=now + timedelta(days=5),
            registration_end_date=now + timedelta(days=1),
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_nonexistent_modality(self):
        adapter, _, _, modality_repository, *_rest = make_adapter()
        modality_repository.find_by_ids.return_value = []

        context = make_context()

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_inactive_modality(self):
        adapter, _, _, modality_repository, *_rest = make_adapter()
        modality_id = uuid4()
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal", active=False)
        ]

        context = make_context(modality_ids=[modality_id])

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_missing_data(self):
        adapter, *_ = make_adapter()
        context = Context()

        with pytest.raises(BusinessException):
            await adapter.execute(context)