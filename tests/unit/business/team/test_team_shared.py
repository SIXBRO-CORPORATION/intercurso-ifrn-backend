from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from business.team._shared import evaluate_submit_eligibility
from domain.enums.gender import Gender
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_open_season(season_id):
    now = datetime.now(timezone.utc)
    return Season(
        id=season_id,
        name="Intercurso 2026",
        status=SeasonStatus.REGISTRATION_OPEN,
        registration_start_date=now - timedelta(days=1),
        registration_end_date=now + timedelta(days=10),
    )


@pytest.mark.unit
class TestEvaluateSubmitEligibility:
    def test_blocks_when_team_not_in_draft(self):
        team = Team(id=uuid4(), status=TeamStatus.SUBMITTED)

        can_submit, reason = evaluate_submit_eligibility(
            team, [], None, None, None, datetime.now(timezone.utc)
        )

        assert can_submit is False
        assert "rascunho" in reason

    def test_blocks_when_no_matching_active_season(self):
        team = Team(id=uuid4(), season_id=uuid4(), status=TeamStatus.DRAFT)

        can_submit, reason = evaluate_submit_eligibility(
            team, [], None, None, None, datetime.now(timezone.utc)
        )

        assert can_submit is False
        assert "temporada" in reason

    def test_blocks_when_registration_window_not_open_yet(self):
        season_id = uuid4()
        team = Team(id=uuid4(), season_id=season_id, status=TeamStatus.DRAFT)
        season = make_open_season(season_id)
        season.registration_start_date = datetime.now(timezone.utc) + timedelta(days=1)

        can_submit, reason = evaluate_submit_eligibility(
            team, [], None, season, None, datetime.now(timezone.utc)
        )

        assert can_submit is False
        assert "ainda não foi iniciado" in reason

    def test_blocks_when_below_minimum_members(self):
        season_id = uuid4()
        team = Team(id=uuid4(), season_id=season_id, status=TeamStatus.DRAFT)
        season = make_open_season(season_id)
        modality = Modality(id=uuid4(), name="Futsal", min_members=5, max_members=10)
        members = [TeamMember(id=uuid4(), user_id=uuid4())]

        can_submit, reason = evaluate_submit_eligibility(
            team, members, modality, season, None, datetime.now(timezone.utc)
        )

        assert can_submit is False
        assert "Faltam 4" in reason

    def test_blocks_when_mixed_modality_gender_quota_not_met(self):
        season_id = uuid4()
        team = Team(id=uuid4(), season_id=season_id, status=TeamStatus.DRAFT)
        season = make_open_season(season_id)
        modality = Modality(
            id=uuid4(),
            name="Voleibol",
            min_members=6,
            max_members=12,
            gender_mode=ModalityGenderMode.MIXED,
            min_male_members=4,
            min_female_members=2,
        )
        members = [TeamMember(id=uuid4(), user_id=uuid4()) for _ in range(6)]
        member_users = [User(id=m.user_id, gender=Gender.MALE) for m in members[:5]] + [
            User(id=members[5].user_id, gender=Gender.FEMALE)
        ]

        can_submit, reason = evaluate_submit_eligibility(
            team, members, modality, season, member_users, datetime.now(timezone.utc)
        )

        assert can_submit is False
        assert "feminino" in reason

    def test_allows_when_all_rules_met(self):
        season_id = uuid4()
        team = Team(id=uuid4(), season_id=season_id, status=TeamStatus.DRAFT)
        season = make_open_season(season_id)
        modality = Modality(id=uuid4(), name="Futsal", min_members=5, max_members=10)
        members = [TeamMember(id=uuid4(), user_id=uuid4()) for _ in range(5)]

        can_submit, reason = evaluate_submit_eligibility(
            team, members, modality, season, None, datetime.now(timezone.utc)
        )

        assert can_submit is True
        assert reason is None
