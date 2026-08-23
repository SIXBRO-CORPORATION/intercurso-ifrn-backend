from uuid import UUID

from core.business.team.get_team_details_port import GetTeamDetailsPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class GetTeamDetailsAdapter(GetTeamDetailsPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Identificador do time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        requesting_role = context.get_property("requesting_user_role", UserRole)
        is_monitor_operation = requesting_role in (UserRole.MONITOR, UserRole.ADMIN)

        if not is_monitor_operation:
            is_member = await self.team_member_repository.exists_by_team_and_user(
                team_id, requesting_user_id
            )
            if not is_member:
                raise BusinessException(
                    "Você não tem permissão para visualizar este time"
                )

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        member_user_ids = [member.user_id for member in members]
        member_users = (
            await self.user_repository.find_by_ids(member_user_ids)
            if member_user_ids
            else []
        )
        member_users_by_id = {user.id: user for user in member_users}

        modality = await self.modality_repository.get(team.modality_id)
        owner_user = member_users_by_id.get(team.owner_id) or (
            await self.user_repository.get(team.owner_id) if team.owner_id else None
        )
        captain_user = (
            member_users_by_id.get(team.captain_id)
            if team.captain_id
            else None
        )
        if team.captain_id and captain_user is None:
            captain_user = await self.user_repository.get(team.captain_id)

        context.put_property("modality", modality)
        context.put_property("members", members)
        context.put_property("member_users_by_id", member_users_by_id)
        context.put_property("owner_user", owner_user)
        context.put_property("captain_user", captain_user)

        return team
