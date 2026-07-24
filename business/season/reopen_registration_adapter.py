from datetime import datetime, timezone
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.season.reopen_registration_port import ReopenRegistrationPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


class ReopenRegistrationAdapter(ReopenRegistrationPort):
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
        new_end = context.get_property("new_registration_end_date", datetime)
        reopened_by = context.get_property("reopened_by", UUID)

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


        reopening_user = (
            await self.user_repository.get(reopened_by) if reopened_by else None
        )
        actor_role = (
            reopening_user.role.value
            if reopening_user is not None and reopening_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.SEASON_REGISTRATION_REOPENED,
            description=(
                f"Inscrições da temporada '{updated_season.name}' reabertas "
                f"até {updated_season.registration_end_date}"
            ),
            actor_id=reopened_by,
            actor_role=actor_role,
        )

        return updated_season