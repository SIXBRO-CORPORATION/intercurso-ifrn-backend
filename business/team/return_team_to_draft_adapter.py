from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.return_team_to_draft_port import ReturnTeamToDraftPort
from core.context import Context
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.not_found_exception import NotFoundException
from domain.team.team import Team


class ReturnTeamToDraftAdapter(ReturnTeamToDraftPort):

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
            raise NotFoundException("Time não encontrado")

        if team.owner_id != requesting_user_id:
            raise BusinessException("Apenas o dono do time pode devolvê-lo para rascunho")

        if team.status != TeamStatus.REJECTED:
            raise BusinessException(
                "Somente times rejeitados podem ser devolvidos para rascunho"
            )

        team.status = TeamStatus.DRAFT
        team.token_active = True

        saved_team = await self.team_repository.save(team)

        await self.audit_logger.log(
            action=AuditAction.TEAM_RETURNED_TO_DRAFT,
            description=f"Time '{saved_team.name}' devolvido para rascunho após rejeição",
            actor_id=requesting_user_id,
        )

        return saved_team
