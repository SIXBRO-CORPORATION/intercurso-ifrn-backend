from datetime import datetime
from uuid import UUID

from core.business.team.approve_team_port import ApproveTeamPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team


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

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        if not members:
            raise BusinessException("Time não possui membros")

        pending_donations = [
            member
            for member in members
            if member.donation_status != DonationStatus.DONATION_CONFIRMED
        ]
        if pending_donations:
            raise BusinessException(
                "Todos os membros devem ter a doação confirmada antes da aprovação"
            )

        team.status = TeamStatus.APPROVED
        team.approved_at = datetime.now()
        team.approved_by = approved_by_user_id

        return await self.team_repository.save(team)
