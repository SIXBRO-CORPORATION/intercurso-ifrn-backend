from datetime import datetime
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.delete_team_port import DeleteTeamPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class DeleteTeamAdapter(DeleteTeamPort):
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
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.owner_id != requesting_user_id:
            raise BusinessException("Apenas o dono do time pode excluí-lo")

        if team.status != TeamStatus.DRAFT:
            raise BusinessException("Este time não aceita mais alterações")

        members = await self.team_member_repository.find_members_by_team_id(team_id)

        team.deleted_at = datetime.now()
        await self.team_repository.save(team)

        member_user_ids = [member.user_id for member in members]
        users_with_active_teams = (
            await self.team_repository.find_user_ids_with_active_teams(member_user_ids)
        )
        await self.user_repository.clear_atleta(
            [uid for uid in member_user_ids if uid not in users_with_active_teams]
        )

        requesting_user = await self.user_repository.get(requesting_user_id)
        await self.audit_logger.log(
            action=AuditAction.TEAM_DELETED,
            description=f"Time '{team.name}' excluído",
            actor_id=requesting_user_id,
            actor=requesting_user,
        )

        return team
