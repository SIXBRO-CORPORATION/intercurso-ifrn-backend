import uuid
from contextlib import suppress
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.season.create_season_port import CreateSeasonPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.storage.file_storage_port import FileStoragePort
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.conflict_exception import ConflictException
from domain.season.season import Season
from domain.season.season_modality import SeasonModality
from domain.season.season_rules_document import (
    MAX_SEASON_RULES_DOCUMENT_BYTES,
    SEASON_RULES_DOCUMENT_FOLDER,
    sniff_season_rules_document,
)


class CreateSeasonAdapter(CreateSeasonPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        audit_logger: AuditLogger,
        file_storage: FileStoragePort,
    ):
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.modality_repository = modality_repository
        self.audit_logger = audit_logger
        self.file_storage = file_storage

    async def execute(self, context: Context) -> Season:
        season = context.get_data(Season)
        modality_ids: List[UUID] = context.get_property("modality_ids", list) or []
        open_immediately = bool(
            context.get_property("open_immediately", bool) or False
        )
        created_by = context.get_property("created_by", UUID)

        rules_document_bytes = context.get_property("rules_document_bytes", bytes)
        rules_document_type = None
        if rules_document_bytes:
            if len(rules_document_bytes) > MAX_SEASON_RULES_DOCUMENT_BYTES:
                raise BusinessException(
                    "Arquivo de regulamento excede o tamanho máximo permitido de 10MB"
                )
            rules_document_type = sniff_season_rules_document(rules_document_bytes)
            if rules_document_type is None:
                raise BusinessException(
                    "Formato de arquivo inválido. Envie um arquivo PDF ou DOCX"
                )

        if season is None:
            raise BusinessException("Dados da temporada são obrigatórios")

        if await self.season_repository.exists_unfinished_season():
            raise ConflictException(
                "Finalize a temporada atual antes de criar uma nova temporada"
            )

        if not season.name or not season.name.strip():
            raise BusinessException("Nome da temporada não pode estar vazio")

        current_year = datetime.now().year
        if season.year is None or season.year < current_year:
            raise BusinessException(
                "Ano da temporada deve ser maior ou igual ao ano atual"
            )

        if not modality_ids:
            raise BusinessException("Ao menos uma modalidade deve ser selecionada")

        now = datetime.now(timezone.utc)

        if not open_immediately:
            if (
                season.registration_start_date is None
                or season.registration_start_date < now
            ):
                raise BusinessException(
                    "Data de abertura das inscrições deve ser maior ou igual à data atual"
                )

        if season.registration_end_date is None:
            raise BusinessException(
                "Data de encerramento das inscrições é obrigatória"
            )

        registration_start_reference = (
            now if open_immediately else season.registration_start_date
        )
        if season.registration_end_date <= registration_start_reference:
            raise BusinessException(
                "Data de encerramento deve ser maior que a data de abertura"
            )

        found_modalities = await self.modality_repository.find_by_ids(modality_ids)
        modalities_by_id = {modality.id: modality for modality in found_modalities}

        for modality_id in modality_ids:
            modality = modalities_by_id.get(modality_id)
            if modality is None:
                raise BusinessException(
                    f"Modalidade {modality_id} não encontrada"
                )
            if not modality.active:
                raise BusinessException(
                    f"Modalidade '{modality.name}' está inativa e não pode ser selecionada"
                )


        rules_document_key = None
        if rules_document_type is not None:
            content_type, ext = rules_document_type
            rules_document_key = f"{SEASON_RULES_DOCUMENT_FOLDER}/{uuid.uuid4()}.{ext}"
            await self.file_storage.upload(
                file_bytes=rules_document_bytes,
                object_key=rules_document_key,
                content_type=content_type,
            )

        new_season = Season(
            name=season.name.strip(),
            year=season.year,
            status=(
                SeasonStatus.REGISTRATION_OPEN
                if open_immediately
                else SeasonStatus.DRAFT
            ),
            registration_start_date=(
                now
                if open_immediately
                else season.registration_start_date
            ),
            registration_end_date=season.registration_end_date,
            registration_opened_at=season.registration_opened_at,
            rules_document=rules_document_key,
            created_by=created_by,
        )
        # Rascunho nasce inativo (UC001 passo 8). Só a abertura torna a temporada ativa.
        new_season.active = open_immediately

        try:
            saved_season = await self.season_repository.save(new_season)

            season_modalities = await self.season_modality_repository.insert_all(
                [
                    SeasonModality(season_id=saved_season.id, modality_id=modality_id)
                    for modality_id in modality_ids
                ]
            )
        except Exception:
            if rules_document_key is not None:
                with suppress(Exception):
                    await self.file_storage.delete(rules_document_key)
            raise

        context.put_property("season_modalities", season_modalities)

        await self.audit_logger.log(
            action=AuditAction.SEASON_CREATED,
            description=(
                f"Temporada '{saved_season.name}' ({saved_season.year}) criada"
                + (" com abertura imediata das inscrições" if open_immediately else "")
            ),
            actor_id=created_by,
        )

        return saved_season