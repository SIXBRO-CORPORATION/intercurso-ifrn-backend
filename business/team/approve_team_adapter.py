from datetime import datetime
from uuid import UUID

from core.business.team.approve_team_port import ApproveTeamPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class ApproveTeamAdapter(ApproveTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository

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

        team.status = TeamStatus.APPROVED
        team.approved_at = datetime.now()
        team.approved_by = approved_by_user_id

        return await self.team_repository.save(team)
