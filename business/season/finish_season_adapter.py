from datetime import datetime
from uuid import UUID

from core.business.season.finish_season_port import FinishSeasonPort
from core.context import Context
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


class FinishSeasonAdapter(FinishSeasonPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        team_repository: TeamRepositoryPort,
    ):
        self.season_repository = season_repository
        self.team_repository = team_repository

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)
        confirmation_name = context.get_property("confirmation_name", str)

        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        if confirmation_name is None or confirmation_name == "":
            raise BusinessException(
                "Nome de confirmação é obrigatório para finalizar a temporada"
            )

        season = await self.season_repository.get(season_id)
        if season is None:
            raise BusinessException("Temporada não encontrada")

        if season.status != SeasonStatus.IN_PROGRESS:
            raise BusinessException(
                "Apenas temporadas em andamento (IN_PROGRESS) podem ser finalizadas"
            )

        if confirmation_name != season.name:
            raise BusinessException(
                "Nome de confirmação não corresponde ao nome da temporada"
            )

        # TODO (débito técnico assumido nesta fase, mesmo padrão das demais
        # regras "futuras" do UC001/UC002): validar que todos os jogos da
        # temporada estão finalizados (Fluxo Alternativo 3 / Regra 3). Essa
        # validação depende da camada de Partidas (Fase 5 do planejamento),
        # que ainda não existe no projeto.

        now = datetime.now()
        season.status = SeasonStatus.FINISHED
        season.finished_at = now
        season.active = False

        updated_season = await self.season_repository.save(season)

        teams = await self.team_repository.find_by_season_id(season_id)
        for team in teams:
            if team.token_active:
                team.token_active = False
                await self.team_repository.save(team)

        # TODO (débito técnico assumido nesta fase, mesmo padrão do UC001/
        # UC002): registrar a operação em auditoria (monitor responsável,
        # data/hora, ação). Não há infraestrutura de auditoria no projeto
        # ainda.

        return updated_season
