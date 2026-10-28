from datetime import datetime, timezone
from uuid import UUID

from business.team._shared import evaluate_approve_eligibility
from core.business.audit.audit_logger import AuditLogger
from core.business.team.approve_team_port import ApproveTeamPort
from core.messaging.team_notification_port import TeamNotificationPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class ApproveTeamAdapter(ApproveTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        audit_logger: AuditLogger,
        team_notification: TeamNotificationPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.modality_repository = modality_repository
        self.audit_logger = audit_logger
        self.team_notification = team_notification

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        approved_by_user_id = context.get_property("approved_by_user_id", UUID)

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.status != TeamStatus.SUBMITTED:
            raise BusinessException(
                "Somente times com aprovação pendente podem ser aprovados"
            )

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        users = await self.user_repository.find_by_ids([m.user_id for m in members])
        modality = await self.modality_repository.get(team.modality_id)

        can_approve, blocked_reason = evaluate_approve_eligibility(
            team, members, modality, users
        )
        if not can_approve:
            raise BusinessException(blocked_reason)

        team.status = TeamStatus.APPROVED
        team.approved_at = datetime.now(timezone.utc)
        team.approved_by = approved_by_user_id

        saved_team = await self.team_repository.save(team)

        await self.audit_logger.log(
            action=AuditAction.TEAM_APPROVED,
            description=f"Time '{saved_team.name}' aprovado",
            actor_id=approved_by_user_id,
        )

        await self.team_notification.team_approved(
            saved_team, [member.user_id for member in members]
        )

        return saved_team