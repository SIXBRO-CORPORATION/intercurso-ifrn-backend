from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.select_captain_port import SelectCaptainPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class SelectCaptainAdapter(SelectCaptainPort):
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
        target_user_id = context.get_property("target_user_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None or target_user_id is None:
            raise BusinessException("Time e membro alvo são obrigatórios")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.owner_id != requesting_user_id:
            raise BusinessException("Apenas o dono do time pode selecionar o capitão")

        if team.status != TeamStatus.DRAFT:
            raise BusinessException("Este time não aceita mais alterações")

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        target_member = next(
            (member for member in members if member.user_id == target_user_id), None
        )
        if target_member is None:
            raise BusinessException("Esse usuário não é membro do time")

        team.captain_id = target_user_id
        saved_team = await self.team_repository.save(team)

        context.put_property("captain_member", target_member)

        requesting_user = await self.user_repository.get(requesting_user_id)
        actor_role = (
            requesting_user.role.value
            if requesting_user is not None and requesting_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.TEAM_CAPTAIN_SELECTED,
            description=f"Capitão selecionado para o time '{saved_team.name}'",
            actor_id=requesting_user_id,
            actor_role=actor_role,
        )

        return saved_team