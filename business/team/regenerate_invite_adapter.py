import secrets
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.regenerate_invite_port import RegenerateInvitePort
from core.context import Context
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class RegenerateInviteAdapter(RegenerateInvitePort):
    def __init__(self, team_repository: TeamRepositoryPort, audit_logger: AuditLogger):
        self.team_repository = team_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.owner_id != requesting_user_id:
            raise BusinessException("Apenas o dono do time pode gerar um novo convite")

        if team.status != TeamStatus.DRAFT:
            raise BusinessException("Este time não aceita mais alterações")

        team.invite_token = secrets.token_urlsafe(16)
        team.token_active = True

        saved_team = await self.team_repository.save(team)

        await self.audit_logger.log(
            action=AuditAction.TEAM_INVITE_REGENERATED,
            description=f"Convite do time '{saved_team.name}' regenerado",
            actor_id=requesting_user_id,
        )

        return saved_team
