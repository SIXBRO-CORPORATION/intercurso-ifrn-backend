from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.season.create_season_adapter import CreateSeasonAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.conflict_exception import ConflictException
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.season.season_modality import SeasonModality


def make_adapter():
    season_repository = AsyncMock()
    season_repository.exists_unfinished_season.return_value = False
    season_modality_repository = AsyncMock()
    modality_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    file_storage = AsyncMock()
    file_storage.upload.side_effect = lambda **kw: kw["object_key"]

    adapter = CreateSeasonAdapter(
        season_repository,
        season_modality_repository,
        modality_repository,
        audit_logger,
        file_storage,
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
        rules_document_bytes=None,
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
    if rules_document_bytes is not None:
        context.put_property("rules_document_bytes", rules_document_bytes)
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
        season_modality_repository.insert_all.side_effect = lambda models: models

        context = make_context(modality_ids=[modality_id])

        result = await adapter.execute(context)

        assert result is not None
        season_repository.save.assert_awaited_once()
        season_modality_repository.insert_all.assert_awaited_once()
        season_repository.exists_unfinished_season.assert_awaited_once()
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

    @pytest.mark.parametrize("open_immediately", [False, True])
    async def test_creation_is_blocked_when_there_is_an_unfinished_season(
        self, open_immediately
    ):
        adapter, season_repository, *_ = make_adapter()
        season_repository.exists_unfinished_season.return_value = True

        with pytest.raises(ConflictException, match="Finalize a temporada atual"):
            await adapter.execute(
                make_context(
                    modality_ids=[uuid4()],
                    open_immediately=open_immediately,
                )
            )

        season_repository.save.assert_not_awaited()

    async def test_open_immediately_creates_season_active_when_all_are_finished(self):
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


PDF = b"%PDF-1.4" + b"0" * 32
DOCX = b"PK\x03\x04" + b"0" * 32


def arrange_valid_flow(parts, rules_document_bytes):
    (
        adapter,
        season_repository,
        season_modality_repository,
        modality_repository,
        user_repository,
        audit_logger,
    ) = parts
    modality_id = uuid4()
    modality_repository.find_by_ids.return_value = [
        Modality(id=modality_id, name="Futsal", min_members=5, max_members=10, active=True)
    ]
    season_repository.save.side_effect = lambda s: s
    season_modality_repository.insert_all.side_effect = lambda models: models
    context = make_context(
        modality_ids=[modality_id], rules_document_bytes=rules_document_bytes
    )
    return adapter, season_repository, context


@pytest.mark.unit
class TestCreateSeasonRulesDocument:
    @pytest.mark.parametrize(
        "data,ext,ctype",
        [
            (PDF, "pdf", "application/pdf"),
            (
                DOCX,
                "docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ],
    )
    async def test_uploads_rules_document_and_stores_object_key(self, data, ext, ctype):
        adapter, _, context = arrange_valid_flow(make_adapter(), data)

        season = await adapter.execute(context)

        kwargs = adapter.file_storage.upload.await_args.kwargs
        assert kwargs["object_key"].startswith("seasons/rules-documents/")
        assert kwargs["object_key"].endswith(f".{ext}")
        assert kwargs["content_type"] == ctype and kwargs["file_bytes"] == data
        assert season.rules_document == kwargs["object_key"]

    async def test_no_rules_document_means_no_upload(self):
        adapter, _, context = arrange_valid_flow(make_adapter(), None)

        season = await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()
        assert season.rules_document is None

    async def test_rejects_invalid_file_before_any_io(self):
        parts = make_adapter()
        adapter, season_repository, context = arrange_valid_flow(
            parts, b"not a pdf nor docx"
        )

        with pytest.raises(BusinessException, match="Formato de arquivo inválido"):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()
        season_repository.save.assert_not_awaited()

    async def test_rejects_oversized_rules_document(self):
        adapter, _, context = arrange_valid_flow(
            make_adapter(), PDF + b"0" * (10 * 1024 * 1024)
        )

        with pytest.raises(BusinessException, match="10MB"):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()

    async def test_business_rejection_does_not_upload(self):
        parts = make_adapter()
        adapter, season_repository, context = arrange_valid_flow(parts, PDF)
        season_repository.exists_unfinished_season.return_value = True

        with pytest.raises(ConflictException, match="Finalize a temporada atual"):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()

    async def test_deletes_uploaded_rules_document_when_save_fails(self):
        adapter, season_repository, context = arrange_valid_flow(make_adapter(), PDF)
        season_repository.save.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError):
            await adapter.execute(context)

        key = adapter.file_storage.upload.await_args.kwargs["object_key"]
        adapter.file_storage.delete.assert_awaited_once_with(key)