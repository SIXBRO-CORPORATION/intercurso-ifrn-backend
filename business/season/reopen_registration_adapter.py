from datetime import datetime, timezone
from uuid import UUID

from core.business.season.reopen_registration_port import ReopenRegistrationPort
from core.context import Context
from core.persistence.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season


class ReopenRegistrationAdapter(ReopenRegistrationPort):
    def __init__(self, season_repository: SeasonRepositoryPort):
        self.season_repository = season_repository

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)
        new_end = context.get_property("new_registration_end_date", datetime)

        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        if new_end is None:
            raise BusinessException(
                "Nova data de encerramento é obrigatória para reabrir as inscrições"
            )

        season = await self.season_repository.get(season_id)
        if season is None:
            raise BusinessException("Temporada não encontrada")

        if season.status != SeasonStatus.REGISTRATION_CLOSED:
            raise BusinessException(
                "Apenas temporadas com inscrições encerradas podem ser reabertas"
            )

        now = datetime.now(timezone.utc)
        if new_end <= now:
            raise BusinessException(
                "Nova data de encerramento deve ser maior que a data atual"
            )

        if (
            season.registration_start_date is not None
            and new_end <= season.registration_start_date
        ):
            raise BusinessException(
                "Nova data de encerramento deve ser maior que a data de abertura"
            )

        season.status = SeasonStatus.REGISTRATION_OPEN
        season.registration_end_date = new_end
        season.registration_closed_at = None

        updated_season = await self.season_repository.save(season)

        # TODO (débito técnico assumido nesta fase, mesmo padrão do UC001):
        # enviar notificação aos alunos e registrar a operação em auditoria
        # (regras 17 e 22/23). O novo agendamento do job de encerramento
        # (regra 16) é natural: o job de encerramento faz polling em
        # temporadas REGISTRATION_OPEN, então esta temporada volta a ser
        # verificada automaticamente no próximo ciclo.

        return updated_season
