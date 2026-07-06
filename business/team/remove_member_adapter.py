from uuid import UUID

from core.business.team.remove_member_port import RemoveMemberPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team_member import TeamMember


class RemoveMemberAdapter(RemoveMemberPort):
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
        target_user_id = context.get_property("target_user_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None or target_user_id is None:
            raise BusinessException("Time e membro alvo são obrigatórios")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        requesting_user = await self.user_repository.get(requesting_user_id)
        if requesting_user is None:
            raise BusinessException("Usuário não encontrado")

        is_monitor_operation = requesting_user.role in (
            UserRole.MONITOR,
            UserRole.ADMIN,
        )

        # Monitor pode remover membros em qualquer status do time (BR13/25).
        # Owner só pode remover membros durante DRAFT (BR12).
        if not is_monitor_operation:
            if team.owner_id != requesting_user_id:
                raise BusinessException(
                    "Apenas o dono do time ou um monitor podem remover membros"
                )

            if team.status != TeamStatus.DRAFT:
                raise BusinessException("Este time não aceita mais alterações")

        if target_user_id == team.owner_id:
            raise BusinessException(
                "O dono do time não pode ser removido. Delete o time para isso."
            )

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        target_member = next(
            (member for member in members if member.user_id == target_user_id), None
        )
        if target_member is None:
            raise BusinessException("Esse usuário não é membro do time")

        await self.team_member_repository.delete(target_member.id)

        if team.captain_id == target_user_id:
            team.captain_id = None
            team = await self.team_repository.save(team)

        other_teams = await self.team_repository.find_teams_by_user_id(target_user_id)
        target_user = await self.user_repository.get(target_user_id)
        if target_user is not None and not other_teams and target_user.atleta:
            target_user.atleta = False
            await self.user_repository.save(target_user)

        context.put_property("team", team)
        context.put_property("removed_user", target_user)
        context.put_property("administrative_operation", is_monitor_operation)

        # TODO (débito técnico assumido, mesmo padrão das demais fases):
        # registrar a operação em auditoria (autor, data/hora, ação,
        # incluindo o marcador de operação administrativa quando aplicável).
        # Não há infraestrutura de auditoria no projeto ainda.

        return target_member
