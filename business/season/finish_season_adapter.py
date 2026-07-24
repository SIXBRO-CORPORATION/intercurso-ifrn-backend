from datetime import datetime
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.season.finish_season_port import FinishSeasonPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


class FinishSeasonAdapter(FinishSeasonPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        team_repository: TeamRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.season_repository = season_repository
        self.team_repository = team_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)
        confirmation_name = context.get_property("confirmation_name", str)
        finished_by = context.get_property("finished_by", UUID)

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

        finishing_user = (
            await self.user_repository.get(finished_by) if finished_by else None
        )
        actor_role = (
            finishing_user.role.value
            if finishing_user is not None and finishing_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.SEASON_FINISHED,
            description=f"Temporada '{updated_season.name}' finalizada",
            actor_id=finished_by,
            actor_role=actor_role,
        )

        return updated_season