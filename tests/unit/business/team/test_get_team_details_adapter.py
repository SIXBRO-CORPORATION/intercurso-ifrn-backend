from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.get_team_details_adapter import GetTeamDetailsAdapter
from core.context import Context
from domain.bracket.bracket_group import BracketGroup
from domain.enums.donation_status import DonationStatus
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    modality_repository = AsyncMock()
    season_repository = AsyncMock()
    match_repository = AsyncMock()
    bracket_group_repository = AsyncMock()

    # Por padrão nenhuma temporada ativa e nenhuma próxima partida, para que
    # os testes que não se importam com can_submit/next_match não precisem
    # configurar esses mocks.
    season_repository.find_active_season.return_value = None
    match_repository.find_next_match_by_team.return_value = None

    adapter = GetTeamDetailsAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        modality_repository,
        season_repository,
        match_repository,
        bracket_group_repository,
    )
    return (
        adapter,
        team_repository,
        team_member_repository,
        user_repository,
        modality_repository,
        season_repository,
        match_repository,
        bracket_group_repository,
    )


def make_context(team_id, requesting_user_id=None, requesting_user_role=UserRole.USER):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property(
        "requesting_user_id", requesting_user_id if requesting_user_id else uuid4()
    )
    context.put_property("requesting_user_role", requesting_user_role)
    return context


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
class TestGetTeamDetailsAdapter:
    async def test_monitor_can_view_any_team(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            *_rest,
        ) = make_adapter()
        owner_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=owner_id)
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(team.id, requesting_user_role=UserRole.MONITOR)
        result = await adapter.execute(context)

        assert result is team
        team_member_repository.exists_by_team_and_user.assert_not_called()

    async def test_member_can_view_own_team(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            *_rest,
        ) = make_adapter()
        requesting_user_id = uuid4()
        owner_id = uuid4()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=owner_id)
        member = TeamMember(
            id=uuid4(),
            team_id=team.id,
            user_id=requesting_user_id,
            role=TeamMemberRole.MEMBER,
            donation_status=DonationStatus.DONATION_CONFIRMED,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = [member]
        user_repository.find_by_ids.return_value = [
            User(id=requesting_user_id, name="Membro", matricula="123")
        ]
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(
            team.id, requesting_user_id=requesting_user_id, requesting_user_role=UserRole.USER
        )
        result = await adapter.execute(context)

        assert result is team
        members = context.get_property("members", list)
        assert len(members) == 1

    async def test_blocks_non_member_student(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            *_rest,
        ) = make_adapter()
        team = Team(id=uuid4(), name="Time A", modality_id=uuid4(), owner_id=uuid4())
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = False

        context = make_context(team.id, requesting_user_role=UserRole.USER)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_team_not_found(self):
        (adapter, team_repository, *_rest) = make_adapter()
        team_repository.get.return_value = None

        context = make_context(uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_team_id_missing(self):
        (adapter, *_rest) = make_adapter()
        context = Context()
        context.put_property("requesting_user_id", uuid4())
        context.put_property("requesting_user_role", UserRole.USER)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_draft_team_exposes_can_submit_true_when_eligible(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            season_repository,
            *_rest,
        ) = make_adapter()
        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Time A",
            modality_id=uuid4(),
            owner_id=owner_id,
            season_id=season_id,
            status=TeamStatus.DRAFT,
        )
        members = [
            TeamMember(
                id=uuid4(),
                team_id=team.id,
                user_id=uuid4(),
                role=TeamMemberRole.MEMBER,
                donation_status=DonationStatus.PENDING_DONATION,
            )
            for _ in range(5)
        ]
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = members
        user_repository.find_by_ids.return_value = [
            User(id=m.user_id, name="Membro", matricula="123") for m in members
        ]
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )
        season_repository.find_active_season.return_value = make_open_season(season_id)

        context = make_context(team.id, requesting_user_role=UserRole.USER)
        await adapter.execute(context)

        assert context.get_property("can_submit", bool) is True
        assert context.get_property("submit_blocked_reason", str) is None

    async def test_draft_team_exposes_submit_blocked_reason_when_below_minimum(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            season_repository,
            *_rest,
        ) = make_adapter()
        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Time A",
            modality_id=uuid4(),
            owner_id=owner_id,
            season_id=season_id,
            status=TeamStatus.DRAFT,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )
        season_repository.find_active_season.return_value = make_open_season(season_id)

        context = make_context(team.id, requesting_user_role=UserRole.USER)
        await adapter.execute(context)

        assert context.get_property("can_submit", bool) is False
        assert "Faltam" in context.get_property("submit_blocked_reason", str)

    async def test_non_draft_team_does_not_query_season_for_can_submit(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            season_repository,
            *_rest,
        ) = make_adapter()
        owner_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Time A",
            modality_id=uuid4(),
            owner_id=owner_id,
            status=TeamStatus.SUBMITTED,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(team.id, requesting_user_role=UserRole.USER)
        await adapter.execute(context)

        season_repository.find_active_season.assert_not_called()
        assert context.get_property("can_submit", bool) is False

    async def test_approved_team_exposes_next_match(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            season_repository,
            match_repository,
            bracket_group_repository,
        ) = make_adapter()
        owner_id = uuid4()
        opponent_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Time A",
            modality_id=uuid4(),
            owner_id=owner_id,
            status=TeamStatus.APPROVED,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        match = Match(
            id=uuid4(),
            bracket_id=uuid4(),
            bracket_group_id=uuid4(),
            team1_id=team.id,
            team2_id=opponent_id,
            match_type=MatchType.SEMIFINAL,
            status=MatchStatus.SCHEDULED,
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=2),
        )
        match_repository.find_next_match_by_team.return_value = match
        bracket_group_repository.get.return_value = BracketGroup(
            id=match.bracket_group_id, bracket_id=match.bracket_id, name="Quartas de final"
        )
        team_repository.find_by_ids.return_value = [
            Team(id=opponent_id, name="Time B", modality_id=team.modality_id)
        ]

        context = make_context(team.id, requesting_user_role=UserRole.USER)
        await adapter.execute(context)

        match_repository.find_next_match_by_team.assert_awaited_once_with(team.id)
        assert context.get_property("next_match", Match) is match
        assert context.get_property("next_match_group_name", str) == "Quartas de final"
        next_match_team1 = context.get_property("next_match_team1", Team)
        next_match_team2 = context.get_property("next_match_team2", Team)
        assert next_match_team1.id == team.id
        assert next_match_team2.id == opponent_id

    async def test_draft_team_does_not_query_next_match(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            modality_repository,
            season_repository,
            match_repository,
            *_rest,
        ) = make_adapter()
        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Time A",
            modality_id=uuid4(),
            owner_id=owner_id,
            season_id=season_id,
            status=TeamStatus.DRAFT,
        )
        team_repository.get.return_value = team
        team_member_repository.exists_by_team_and_user.return_value = True
        team_member_repository.find_members_by_team_id.return_value = []
        user_repository.find_by_ids.return_value = []
        user_repository.get.return_value = User(id=owner_id, name="Dono")
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )
        season_repository.find_active_season.return_value = make_open_season(season_id)

        context = make_context(team.id, requesting_user_role=UserRole.USER)
        await adapter.execute(context)

        match_repository.find_next_match_by_team.assert_not_called()
        assert context.get_property("next_match", Match) is None
