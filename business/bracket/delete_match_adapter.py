from uuid import UUID

from core.business.bracket.delete_match_port import DeleteMatchPort
from core.business.audit.audit_logger import AuditLogger
from core.context import Context
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException


class DeleteMatchAdapter(DeleteMatchPort):
    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.match_repository = match_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> bool:
        match_id = context.get_property("match_id", UUID)
        deleted_by = context.get_property("deleted_by", UUID)
        if match_id is None:
            raise BusinessException("Partida é obrigatória")

        match = await self.match_repository.get(match_id)
        if match is None:
            raise BusinessException("Partida não encontrada")

        if match.status != MatchStatus.SCHEDULED:
            raise BusinessException(
                "Somente partidas agendadas (SCHEDULED) podem ser deletadas"
            )

        deleted_count = await self.match_repository.delete(match_id)

        deleting_user = (
            await self.user_repository.get(deleted_by) if deleted_by else None
        )
        actor_role = (
            deleting_user.role.value
            if deleting_user is not None and deleting_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.MATCH_DELETED,
            description=f"Partida {match_id} deletada",
            actor_id=deleted_by,
            actor_role=actor_role,
        )

        return deleted_count > 0