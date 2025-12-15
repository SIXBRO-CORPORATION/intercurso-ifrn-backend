from datetime import datetime
from uuid import UUID

from core.business.team.approve_team_port import ApproveTeamPort
from core.command import R
from core.context import Context
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team


class ApproveTeamAdapter(ApproveTeamPort):
    def __init__(self, repository: TeamRepositoryPort):
        self.repository = repository


    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)

        if team_id is None:
            raise Exception("ID do time é obrigatório")

        team = await self.repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.status == TeamStatus.APPROVED:
            raise BusinessException("Time já está aprovado")

        if team.status == TeamStatus.REJECTED:
            raise BusinessException("Não é possível aprovar um time rejeitado")

        team.status = TeamStatus.APPROVED
        team.modified_at = datetime.now()

        saved_team = await self.repository.save(team)

        context.put_property("team_approved", True)

        return saved_team