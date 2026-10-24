from datetime import datetime
from typing import List, Optional, Tuple

from domain.enums.donation_status import DonationStatus
from domain.enums.gender import Gender
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User
from security.config import settings


def _gender_quota_block_reason(
    modality: Optional[Modality], member_users: Optional[List[User]]
) -> Optional[str]:

    if modality is None or modality.gender_mode != ModalityGenderMode.MIXED:
        return None

    member_users = member_users or []
    male_count = sum(1 for u in member_users if u.gender == Gender.MALE)
    female_count = sum(1 for u in member_users if u.gender == Gender.FEMALE)

    if modality.min_male_members is not None and male_count < modality.min_male_members:
        return (
            f"Modalidade mista: o time precisa de pelo menos "
            f"{modality.min_male_members} integrante(s) do gênero "
            f"masculino. Atualmente tem {male_count}."
        )
    if modality.min_female_members is not None and female_count < modality.min_female_members:
        return (
            f"Modalidade mista: o time precisa de pelo menos "
            f"{modality.min_female_members} integrante(s) do gênero "
            f"feminino. Atualmente tem {female_count}."
        )
    return None


def evaluate_submit_eligibility(
    team: Team,
    members: List[TeamMember],
    modality: Optional[Modality],
    active_season: Optional[Season],
    member_users: Optional[List[User]],
    now: datetime,
) -> Tuple[bool, Optional[str]]:

    if team.status != TeamStatus.DRAFT:
        return False, (
            "Este time já foi submetido ou não está mais em rascunho"
        )

    if active_season is None or active_season.id != team.season_id:
        return False, (
            "A temporada deste time não é a temporada ativa no momento"
        )

    if active_season.status != SeasonStatus.REGISTRATION_OPEN:
        return False, (
            "Período de inscrições encerrado. Não é mais possível submeter times."
        )

    if (
        active_season.registration_start_date
        and now < active_season.registration_start_date
    ):
        return False, "O período de inscrição ainda não foi iniciado"
    if (
        active_season.registration_end_date
        and now > active_season.registration_end_date
    ):
        return False, "O período de inscrição já foi encerrado"

    if modality is not None and len(members) < modality.min_members:
        faltantes = modality.min_members - len(members)
        return False, (
            f"O time precisa de pelo menos {modality.min_members} membros para "
            f"ser submetido. Faltam {faltantes} membro(s)."
        )

    gender_block_reason = _gender_quota_block_reason(modality, member_users)
    if gender_block_reason:
        return False, gender_block_reason

    return True, None


def evaluate_approve_eligibility(
    team: Team,
    members: List[TeamMember],
    modality: Optional[Modality],
    member_users: Optional[List[User]],
) -> Tuple[bool, Optional[str]]:

    if team.status != TeamStatus.SUBMITTED:
        return False, "Somente times com aprovação pendente podem ser aprovados"

    if len(members) == 0:
        return False, "Time não possui membros"

    pending_donations = sum(
        1 for m in members if m.donation_status != DonationStatus.DONATION_CONFIRMED
    )
    if pending_donations > 0:
        return False, "Todos os membros devem ter a doação confirmada antes da aprovação"

    member_users = member_users or []
    users_by_id = {u.id: u for u in member_users}
    irregulares = [
        users_by_id[m.user_id].name
        for m in members
        if m.user_id in users_by_id
        and users_by_id[m.user_id].tipo_usuario == "Aluno"
        and (
            users_by_id[m.user_id].frequencia_percentual is None
            or users_by_id[m.user_id].frequencia_percentual < settings.min_attendance_percent
        )
    ]
    if irregulares:
        return False, (
            f"Membros sem frequência mínima de {settings.min_attendance_percent}% "
            f"(ou ainda não verificada; peça para entrarem no app novamente): "
            f"{', '.join(irregulares)}"
        )

    gender_block_reason = _gender_quota_block_reason(modality, member_users)
    if gender_block_reason:
        return False, f"{gender_block_reason} Não é possível aprovar até que a cota seja atendida."

    return True, None
