from datetime import datetime
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.season.close_registration_port import CloseRegistrationPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


class CloseRegistrationAdapter(CloseRegistrationPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.season_repository = season_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)
        closed_by = context.get_property("closed_by", UUID)

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

        closing_user = (
            await self.user_repository.get(closed_by) if closed_by else None
        )
        actor_role = (
            closing_user.role.value
            if closing_user is not None and closing_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.SEASON_REGISTRATION_CLOSED,
            description=(
                f"Inscrições da temporada '{updated_season.name}' encerradas "
                "antecipadamente"
            ),
            actor_id=closed_by,
            actor_role=actor_role,
        )

        return updated_season