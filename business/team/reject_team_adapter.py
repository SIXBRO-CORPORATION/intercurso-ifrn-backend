from datetime import datetime
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.reject_team_port import RejectTeamPort
from core.context import Context
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.not_found_exception import NotFoundException
from domain.team.team import Team


class RejectTeamAdapter(RejectTeamPort):

    def __init__(self, team_repository: TeamRepositoryPort, audit_logger: AuditLogger):
        self.team_repository = team_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        rejected_by_user_id = context.get_property("rejected_by_user_id", UUID)
        reason = (context.get_property("rejection_reason", str) or "").strip()

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        if not reason:
            raise BusinessException("O motivo da rejeição é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise NotFoundException("Time não encontrado")

        if team.status != TeamStatus.SUBMITTED:
            raise BusinessException(
                "Somente times submetidos para aprovação podem ser rejeitados"
            )

        team.status = TeamStatus.DRAFT
        team.rejected_at = datetime.now()
        team.rejected_by = rejected_by_user_id
        team.rejection_reason = reason
        team.token_active = True
        team.submmited_at = None

        saved_team = await self.team_repository.save(team)

        await self.audit_logger.log(
            action=AuditAction.TEAM_REJECTED,
            description=f"Time '{saved_team.name}' rejeitado e devolvido para rascunho",
            actor_id=rejected_by_user_id,
        )

        return saved_team
