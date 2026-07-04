from datetime import datetime
from typing import List
from uuid import UUID

from core.business.season.create_season_port import CreateSeasonPort
from core.context import Context
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season
from domain.season_modality import SeasonModality


class CreateSeasonAdapter(CreateSeasonPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Season:
        season = context.get_data(Season)
        modality_ids: List[UUID] = context.get_property("modality_ids", list) or []
        open_immediately = bool(
            context.get_property("open_immediately", bool) or False
        )
        created_by = context.get_property("created_by", UUID)

        if season is None:
            raise BusinessException("Dados da temporada são obrigatórios")

        if not season.name or not season.name.strip():
            raise BusinessException("Nome da temporada não pode estar vazio")

        current_year = datetime.now().year
        if season.year is None or season.year < current_year:
            raise BusinessException(
                "Ano da temporada deve ser maior ou igual ao ano atual"
            )

        if not modality_ids:
            raise BusinessException("Ao menos uma modalidade deve ser selecionada")

        now = datetime.now()

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

        for modality_id in modality_ids:
            modality = await self.modality_repository.get(modality_id)
            if modality is None:
                raise BusinessException(
                    f"Modalidade {modality_id} não encontrada"
                )
            if not modality.active:
                raise BusinessException(
                    f"Modalidade '{modality.name}' está inativa e não pode ser selecionada"
                )

        new_season = Season(
            name=season.name.strip(),
            year=season.year,
            registration_start_date=(
                now if open_immediately else season.registration_start_date
            ),
            registration_end_date=season.registration_end_date,
            registration_opened_at=now if open_immediately else None,
            rules_document=season.rules_document,
            created_by=created_by,
            status=(
                SeasonStatus.REGISTRATION_OPEN
                if open_immediately
                else SeasonStatus.DRAFT
            ),
            active=open_immediately,
        )

        if open_immediately:
            currently_active = await self.season_repository.find_active_season()
            if currently_active is not None:
                currently_active.active = False
                await self.season_repository.save(currently_active)

        saved_season = await self.season_repository.save(new_season)

        season_modalities = []
        for modality_id in modality_ids:
            season_modality = SeasonModality(
                season_id=saved_season.id,
                modality_id=modality_id,
            )
            saved_season_modality = await self.season_modality_repository.save(
                season_modality
            )
            season_modalities.append(saved_season_modality)

        context.put_property("season_modalities", season_modalities)

        # TODO (débito técnico assumido nesta fase): registrar a operação em
        # auditoria (monitor responsável, data/hora, ação) e, em caso de
        # abertura imediata, disparar notificação push "Inscrições abertas!"
        # aos alunos, conforme UC001. Não há infraestrutura de
        # auditoria/notificação no projeto ainda — job de abertura/
        # encerramento automático (regras 11 e 12) tem o mesmo débito.

        return saved_season
