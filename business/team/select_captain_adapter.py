from uuid import UUID

from core.business.team.select_captain_port import SelectCaptainPort
from core.context import Context
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team

class SelectCaptainAdapter(SelectCaptainPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository

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

        # TODO (débito técnico assumido, mesmo padrão das demais fases):
        # registrar a operação em auditoria (autor, data/hora, ação).
        # Não há infraestrutura de auditoria no projeto ainda.

        return saved_team
