from uuid import UUID

from core.business.team.leave_team_port import LeaveTeamPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team_member import TeamMember


class LeaveTeamAdapter(LeaveTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository

    async def execute(self, context: Context) -> TeamMember:
        team_id = context.get_property("team_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.owner_id == requesting_user_id:
            raise BusinessException(
                "O dono do time não pode sair. Delete o time para isso."
            )

        if team.status != TeamStatus.DRAFT:
            raise BusinessException("Este time não aceita mais alterações")

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        member = next(
            (member for member in members if member.user_id == requesting_user_id),
            None,
        )
        if member is None:
            raise BusinessException("Você não é membro deste time")

        await self.team_member_repository.delete(member.id)

        if team.captain_id == requesting_user_id:
            team.captain_id = None
            team = await self.team_repository.save(team)

        other_teams = await self.team_repository.find_teams_by_user_id(
            requesting_user_id
        )
        requesting_user = await self.user_repository.get(requesting_user_id)
        if (
            requesting_user is not None
            and not other_teams
            and requesting_user.atleta
        ):
            requesting_user.atleta = False
            await self.user_repository.save(requesting_user)

        context.put_property("team", team)

        # TODO (débito técnico assumido, mesmo padrão das demais fases):
        # registrar a operação em auditoria (autor, data/hora, ação).
        # Não há infraestrutura de auditoria no projeto ainda.

        return member
