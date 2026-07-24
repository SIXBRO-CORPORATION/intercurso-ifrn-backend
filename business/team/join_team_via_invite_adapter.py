from datetime import datetime, timezone
from uuid import UUID

from core.business.team.join_team_via_invite_port import JoinTeamViaInvitePort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.donation_status import DonationStatus
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team_member import TeamMember


class JoinTeamViaInviteAdapter(JoinTeamViaInvitePort):
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

    async def execute(self, context: Context) -> TeamMember:
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
        if modality is not None and len(members) >= modality.max_members:
            raise BusinessException("Este time já atingiu o limite máximo de membros")

        existing_teams = await self.team_repository.find_teams_by_user_id(
            requesting_user_id
        )
        already_in_modality = any(
            existing_team.season_id == team.season_id
            and existing_team.modality_id == team.modality_id
            for existing_team in existing_teams
        )
        if already_in_modality:
            raise BusinessException(
                "Você já participa de um time nessa modalidade nesta temporada"
            )

        new_member = TeamMember(
            team_id=team.id,
            user_id=requesting_user_id,
            role=TeamMemberRole.MEMBER,
            donation_status=DonationStatus.PENDING_DONATION,
            joined_at=now,
        )
        saved_member = await self.team_member_repository.save(new_member)

        requesting_user = await self.user_repository.get(requesting_user_id)
        if requesting_user is not None and not requesting_user.atleta:
            requesting_user.atleta = True
            await self.user_repository.save(requesting_user)

        # TODO (débito técnico assumido, mesmo padrão das demais fases):
        # registrar a operação em auditoria (aluno, time, data/hora, ação).
        # Não há infraestrutura de auditoria no projeto ainda.

        context.put_property("team", team)

        return saved_member
