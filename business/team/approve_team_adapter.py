from datetime import datetime
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.approve_team_port import ApproveTeamPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from security.config import settings


class ApproveTeamAdapter(ApproveTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

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

        members_count = await self.team_member_repository.count_by_team(team_id)
        if members_count == 0:
            raise BusinessException("Time não possui membros")

        pending_donations_count = (
            await self.team_member_repository.count_pending_donations_by_team(team_id)
        )
        if pending_donations_count > 0:
            raise BusinessException(
                "Todos os membros devem ter a doação confirmada antes da aprovação"
            )

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        users = await self.user_repository.find_by_ids([m.user_id for m in members])
        # Só alunos têm frequência; None (nunca consultada/SUAP falhou) bloqueia.
        irregulares = [
            u.name
            for u in users
            if u.tipo_usuario == "Aluno"
            and (
                u.frequencia_percentual is None
                or u.frequencia_percentual < settings.min_attendance_percent
            )
        ]
        if irregulares:
            raise BusinessException(
                f"Membros sem frequência mínima de {settings.min_attendance_percent}% "
                f"(ou ainda não verificada; peça para entrarem no app novamente): "
                f"{', '.join(irregulares)}"
            )

        team.status = TeamStatus.APPROVED
        team.approved_at = datetime.now()
        team.approved_by = approved_by_user_id

        saved_team = await self.team_repository.save(team)

        await self.audit_logger.log(
            action=AuditAction.TEAM_APPROVED,
            description=f"Time '{saved_team.name}' aprovado",
            actor_id=approved_by_user_id,
        )

        return saved_team