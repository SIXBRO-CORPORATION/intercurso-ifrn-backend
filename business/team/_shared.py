from datetime import datetime
from typing import List, Optional, Tuple

from domain.enums.gender import Gender
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


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

    if modality is not None and modality.gender_mode == ModalityGenderMode.MIXED:
        member_users = member_users or []
        male_count = sum(1 for u in member_users if u.gender == Gender.MALE)
        female_count = sum(1 for u in member_users if u.gender == Gender.FEMALE)

        if (
            modality.min_male_members is not None
            and male_count < modality.min_male_members
        ):
            return False, (
                f"Modalidade mista: o time precisa de pelo menos "
                f"{modality.min_male_members} integrante(s) do gênero "
                f"masculino. Atualmente tem {male_count}."
            )
        if (
            modality.min_female_members is not None
            and female_count < modality.min_female_members
        ):
            return False, (
                f"Modalidade mista: o time precisa de pelo menos "
                f"{modality.min_female_members} integrante(s) do gênero "
                f"feminino. Atualmente tem {female_count}."
            )

    return True, None
