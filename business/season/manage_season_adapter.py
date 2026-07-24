from datetime import datetime, timezone
from uuid import UUID

from core.business.season.manage_season_port import ManageSeasonPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season


class ManageSeasonAdapter(ManageSeasonPort):
    def __init__(self, season_repository: SeasonRepositoryPort):
        self.season_repository = season_repository

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)
        new_start = context.get_property("new_registration_start_date", datetime)
        new_end = context.get_property("new_registration_end_date", datetime)

        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        if new_start is None and new_end is None:
            raise BusinessException(
                "Informe ao menos uma data para atualizar (abertura e/ou encerramento)"
            )

        season = await self.season_repository.get(season_id)
        if season is None:
            raise BusinessException("Temporada não encontrada")

        if season.status not in (SeasonStatus.DRAFT, SeasonStatus.REGISTRATION_OPEN):
            raise BusinessException(
                "Não é possível editar temporada em andamento ou finalizada"
            )

        if season.status == SeasonStatus.REGISTRATION_OPEN and new_start is not None:
            raise BusinessException(
                "Não é possível alterar a data de abertura após o início das inscrições"
            )

        now = datetime.now(timezone.utc)

        if new_start is not None:
            if new_start < now:
                raise BusinessException(
                    "Nova data de abertura das inscrições deve ser maior ou igual à data atual"
                )
            season.registration_start_date = new_start

        effective_start = season.registration_start_date

        if new_end is not None:
            if effective_start is None or new_end <= effective_start:
                raise BusinessException(
                    "Nova data de encerramento deve ser maior que a data de abertura"
                )
            season.registration_end_date = new_end

        updated_season = await self.season_repository.save(season)

        # TODO (débito técnico assumido nesta fase, mesmo padrão do UC001):
        # registrar a alteração em auditoria (monitor responsável, data/hora,
        # datas antigas/novas, motivo informado). Não há infraestrutura de
        # auditoria no projeto ainda.

        return updated_season
