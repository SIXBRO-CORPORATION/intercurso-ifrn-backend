from datetime import datetime
from uuid import UUID

from core.business.team.submit_team_port import SubmitTeamPort
from core.context import Context
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.donation_status import DonationStatus
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team


class SubmitTeamAdapter(SubmitTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        season_repository: SeasonRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.season_repository = season_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.owner_id != requesting_user_id:
            raise BusinessException("Apenas o dono do time pode submeter o time")

        if team.status != TeamStatus.DRAFT:
            raise BusinessException(
                "Este time já foi submetido ou não está mais em rascunho"
            )

        active_season = await self.season_repository.find_active_season()
        if active_season is None or active_season.id != team.season_id:
            raise BusinessException(
                "A temporada deste time não é a temporada ativa no momento"
            )

        if active_season.status != SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Período de inscrições encerrado. Não é mais possível submeter times."
            )

        now = datetime.now()
        if (
            active_season.registration_start_date
            and now < active_season.registration_start_date
        ):
            raise BusinessException("O período de inscrição ainda não foi iniciado")
        if (
            active_season.registration_end_date
            and now > active_season.registration_end_date
        ):
            raise BusinessException("O período de inscrição já foi encerrado")

        members = await self.team_member_repository.find_members_by_team_id(team_id)

        modality = await self.modality_repository.get(team.modality_id)
        if modality is not None and len(members) < modality.min_members:
            faltantes = modality.min_members - len(members)
            raise BusinessException(
                f"O time precisa de pelo menos {modality.min_members} membros para "
                f"ser submetido. Faltam {faltantes} membro(s)."
            )

        team.status = TeamStatus.SUBMITTED
        team.token_active = False
        team.submmited_at = now

        saved_team = await self.team_repository.save(team)

        for member in members:
            if member.donation_status != DonationStatus.PENDING_DONATION:
                member.donation_status = DonationStatus.PENDING_DONATION
                await self.team_member_repository.save(member)

        context.put_property("members", members)

        # TODO (débito técnico assumido, mesmo padrão das demais fases):
        # registrar a operação em auditoria (owner, temporada, data/hora, ação).
        # Notificação ao monitor: escopo futuro (fora do alcance desta fase).
        # Não há infraestrutura de auditoria/notificação no projeto ainda.

        return saved_team
