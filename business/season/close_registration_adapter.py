from datetime import datetime
from uuid import UUID

from core.business.season.close_registration_port import CloseRegistrationPort
from core.context import Context
from core.persistence.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season


class CloseRegistrationAdapter(CloseRegistrationPort):
    def __init__(self, season_repository: SeasonRepositoryPort):
        self.season_repository = season_repository

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)

        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        season = await self.season_repository.get(season_id)
        if season is None:
            raise BusinessException("Temporada não encontrada")

        if season.status != SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Apenas temporadas com inscrições abertas podem ser encerradas antecipadamente"
            )

        season.status = SeasonStatus.REGISTRATION_CLOSED
        season.registration_closed_at = datetime.now()

        updated_season = await self.season_repository.save(season)

        # TODO (débito técnico assumido nesta fase, mesmo padrão do UC001):
        # enviar notificação a alunos e monitores e registrar a operação em
        # auditoria (regras 11 e 22/23). Não há infraestrutura de
        # notificação/auditoria no projeto ainda. O cancelamento do job de
        # encerramento automático (regra 10) é natural: o job faz polling em
        # temporadas com status REGISTRATION_OPEN, então mudar o status já
        # remove esta temporada do próximo ciclo de verificação.

        return updated_season
