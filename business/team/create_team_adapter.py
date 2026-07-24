import secrets
from datetime import datetime, timezone
from uuid import UUID

from core.business.team.create_team_port import CreateTeamPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.donation_status import DonationStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.team.team_member import TeamMember


class CreateTeamAdapter(CreateTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Team:
        team = context.get_data(Team)
        creator_user_id = context.get_property("creator_user_id", UUID)

        if team is None:
            raise BusinessException("Dados do time são obrigatórios")

        if creator_user_id is None:
            raise BusinessException("Usuário criador é obrigatório")

        if team.modality_id is None:
            raise BusinessException("Modalidade é obrigatória")

        active_season = await self.season_repository.find_active_season()

        if active_season is None or active_season.status != SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Não há uma temporada com inscrições abertas no momento"
            )

        now = datetime.now(timezone.utc)
        if active_season.registration_start_date and now < active_season.registration_start_date:
            raise BusinessException("O período de inscrição ainda não foi iniciado")
        if active_season.registration_end_date and now > active_season.registration_end_date:
            raise BusinessException("O período de inscrição já foi encerrado")

        if not await self.modality_repository.exists_by_id(team.modality_id):
            raise BusinessException("Modalidade informada não existe")

        modality_in_season = await self.season_modality_repository.exists_by_season_and_modality(
            active_season.id, team.modality_id
        )
        if not modality_in_season:
            raise BusinessException(
                "Modalidade informada não faz parte da temporada ativa"
            )

        existing_teams = await self.team_repository.find_teams_by_user_id(
            creator_user_id
        )
        already_in_modality = any(
            existing_team.season_id == active_season.id
            and existing_team.modality_id == team.modality_id
            for existing_team in existing_teams
        )
        if already_in_modality:
            raise BusinessException(
                "Você já participa de um time nessa modalidade na temporada ativa"
            )

        new_team = Team(
            name=team.name,
            photo=team.photo,
            season_id=active_season.id,
            modality_id=team.modality_id,
            owner_id=creator_user_id,
            invite_token=secrets.token_urlsafe(16),
            token_active=True,
        )

        saved_team = await self.team_repository.save(new_team)

        owner_member = TeamMember(
            team_id=saved_team.id,
            user_id=creator_user_id,
            role=TeamMemberRole.OWNER,
            donation_status=DonationStatus.PENDING_DONATION,
            joined_at=now,
        )
        saved_owner_member = await self.team_member_repository.save(owner_member)

        creator_user = await self.user_repository.get(creator_user_id)
        if creator_user is not None and not creator_user.atleta:
            creator_user.atleta = True
            await self.user_repository.save(creator_user)

        context.put_property("owner_member", saved_owner_member)
        context.put_property("team_members", [saved_owner_member])

        return saved_team
