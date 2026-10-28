from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.approve_team_adapter import ApproveTeamAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    user_repository.find_by_ids.return_value = []
    modality_repository = AsyncMock()
    modality_repository.get.return_value = None
    audit_logger = AsyncMock()
    adapter = ApproveTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        modality_repository,
        audit_logger,
        AsyncMock(),
    )
    adapter.user_repository = user_repository
    return adapter, team_repository, team_member_repository


def make_context(team_id=None):
    context = Context()
    context.put_property("team_id", team_id if team_id is not None else uuid4())
    context.put_property("approved_by_user_id", uuid4())
    return context


def confirmed_members(count):
    return [
        TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        for _ in range(count)
    ]


@pytest.mark.unit
class TestApproveTeamAdapter:
    async def test_approves_submitted_team_with_all_donations_confirmed(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)

        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = confirmed_members(2)
        team_repository.save.return_value = team

        result = await adapter.execute(make_context(team.id))

        assert result.status == TeamStatus.APPROVED
        assert result.approved_at is not None
        team_repository.save.assert_awaited_once()

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, _team_member_repository = make_adapter()
        team_repository.get.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(make_context())

    async def test_blocks_when_team_not_submitted(self):
        adapter, team_repository, _team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.DRAFT)
        team_repository.get.return_value = team

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_has_no_members(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = []

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_pending_donation_exists(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = [
            TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED),
            TeamMember(user_id=uuid4(), donation_status=DonationStatus.PENDING_DONATION),
        ]

        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_id_is_missing(self):
        adapter, team_repository, _team_member_repository = make_adapter()

        context = Context()
        context.put_property("approved_by_user_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.get.assert_not_awaited()

    @pytest.mark.parametrize("frequencia", [None, 74])
    async def test_blocks_student_below_min_or_unverified_attendance(self, frequencia):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        member = TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        team_member_repository.find_members_by_team_id.return_value = [member]
        adapter.user_repository.find_by_ids.return_value = [
            User(id=member.user_id, name="Fulano", tipo_usuario="Aluno", frequencia_percentual=frequencia)
        ]

        with pytest.raises(BusinessException, match="Fulano"):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()

    async def test_approves_at_min_attendance_and_ignores_non_students(self):
        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team
        team_repository.save.return_value = team
        a = TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        b = TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        team_member_repository.find_members_by_team_id.return_value = [a, b]
        adapter.user_repository.find_by_ids.return_value = [
            User(id=a.user_id, name="Aluno", tipo_usuario="Aluno", frequencia_percentual=75),
            User(id=b.user_id, name="Servidor", tipo_usuario="Servidor"),
        ]

        result = await adapter.execute(make_context(team.id))

        assert result.status == TeamStatus.APPROVED

    async def test_blocks_when_gender_quota_not_satisfied(self):
        from domain.enums.gender import Gender
        from domain.enums.modality_gender_mode import ModalityGenderMode
        from domain.modality.modality import Modality

        adapter, team_repository, team_member_repository = make_adapter()
        team = Team(id=uuid4(), name="Time A", status=TeamStatus.SUBMITTED, modality_id=uuid4())
        team_repository.get.return_value = team
        a = TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        b = TeamMember(user_id=uuid4(), donation_status=DonationStatus.DONATION_CONFIRMED)
        team_member_repository.find_members_by_team_id.return_value = [a, b]
        adapter.user_repository.find_by_ids.return_value = [
            User(id=a.user_id, name="A", tipo_usuario="Aluno", frequencia_percentual=100, gender=Gender.FEMALE),
            User(id=b.user_id, name="B", tipo_usuario="Aluno", frequencia_percentual=100, gender=Gender.FEMALE),
        ]
        adapter.modality_repository.get.return_value = Modality(
            id=team.modality_id,
            gender_mode=ModalityGenderMode.MIXED,
            min_male_members=1,
            min_female_members=1,
        )

        with pytest.raises(BusinessException, match="masculino"):
            await adapter.execute(make_context(team.id))

        team_repository.save.assert_not_awaited()
