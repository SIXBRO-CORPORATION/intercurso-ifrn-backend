from datetime import datetime, timezone
from uuid import UUID

from core.business.team.get_team_invite_info_port import GetTeamInviteInfoPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class GetTeamInviteInfoAdapter(GetTeamInviteInfoPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        season_repository: SeasonRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.season_repository = season_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Team:
        invite_token = context.get_property("invite_token", str)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if not invite_token:
            raise BusinessException("Token de convite é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.find_by_invite_token(invite_token)
        if team is None:
            raise BusinessException("Convite não encontrado")

        if not team.token_active or team.status != TeamStatus.DRAFT:
            raise BusinessException("Este convite não está mais ativo")

        season = await self.season_repository.get(team.season_id)
        if season is None or season.status != SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException("O período de inscrição está fechado")

        now = datetime.now(timezone.utc)
        if season.registration_start_date and now < season.registration_start_date:
            raise BusinessException("O período de inscrição está fechado")
        if season.registration_end_date and now > season.registration_end_date:
            raise BusinessException("O período de inscrição está fechado")

        members = await self.team_member_repository.find_members_by_team_id(team.id)

        already_member = any(
            member.user_id == requesting_user_id for member in members
        )
        if already_member:
            raise BusinessException("Você já é membro deste time")

        modality = await self.modality_repository.get(team.modality_id)
        owner_user = await self.user_repository.get(team.owner_id)
        captain_user = (
            await self.user_repository.get(team.captain_id)
            if team.captain_id
            else None
        )

        context.put_property("modality", modality)
        context.put_property("members_count", len(members))
        context.put_property("owner_user", owner_user)
        context.put_property("captain_user", captain_user)

        return team
