from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.join_team_via_invite_adapter import JoinTeamViaInviteAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.modality import Modality
from domain.season import Season
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    season_repository = AsyncMock()
    modality_repository = AsyncMock()

    adapter = JoinTeamViaInviteAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        modality_repository,
    )
    return (
        adapter,
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        modality_repository,
    )


def make_open_season(season_id=None):
    return Season(
        id=season_id or uuid4(),
        name="Intercurso 2026",
        status=SeasonStatus.REGISTRATION_OPEN,
        registration_start_date=datetime.now() - timedelta(days=1),
        registration_end_date=datetime.now() + timedelta(days=5),
    )


def make_draft_team(season_id=None, modality_id=None, owner_id=None):
    return Team(
        id=uuid4(),
        name="Time A",
        season_id=season_id or uuid4(),
        modality_id=modality_id or uuid4(),
        owner_id=owner_id or uuid4(),
        status=TeamStatus.DRAFT,
        invite_token="abc123",
        token_active=True,
    )


def make_context(invite_token="abc123", requesting_user_id=None):
    context = Context()
    context.put_property("invite_token", invite_token)
    context.put_property(
        "requesting_user_id",
        requesting_user_id if requesting_user_id is not None else uuid4(),
    )
    return context


def setup_happy_path(
    team_repository, team_member_repository, user_repository, season_repository,
    modality_repository, team, season, requesting_user_id, existing_members=None,
    other_teams=None,
):
    team_repository.find_by_invite_token.return_value = team
    season_repository.get.return_value = season
    team_member_repository.find_members_by_team_id.return_value = existing_members or []
    modality_repository.get.return_value = Modality(
        id=team.modality_id, name="Futsal", min_members=5, max_members=10
    )
    team_repository.find_teams_by_user_id.return_value = other_teams or []
    team_member_repository.save.side_effect = lambda member: member
    user_repository.get.return_value = User(id=requesting_user_id, atleta=False)


@pytest.mark.unit
class TestJoinTeamViaInviteAdapter:
    async def test_joins_team_successfully(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        team = make_draft_team(season_id=season.id)
        requesting_user_id = uuid4()
        context = make_context(requesting_user_id=requesting_user_id)

        setup_happy_path(
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
            team,
            season,
            requesting_user_id,
        )

        result = await adapter.execute(context)

        assert result.role == TeamMemberRole.MEMBER
        assert result.donation_status == DonationStatus.PENDING_DONATION
        team_member_repository.save.assert_awaited_once()
        user_repository.save.assert_awaited_once()
        assert context.get_property("team", Team).id == team.id

    async def test_does_not_resave_user_already_atleta(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        team = make_draft_team(season_id=season.id)
        requesting_user_id = uuid4()
        context = make_context(requesting_user_id=requesting_user_id)

        setup_happy_path(
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
            team,
            season,
            requesting_user_id,
        )
        user_repository.get.return_value = User(id=requesting_user_id, atleta=True)

        await adapter.execute(context)

        user_repository.save.assert_not_awaited()

    async def test_blocks_when_token_not_found(self):
        (adapter, team_repository, *_rest) = make_adapter()

        context = make_context()
        team_repository.find_by_invite_token.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_invite_inactive(self):
        (adapter, team_repository, *_rest) = make_adapter()

        team = make_draft_team()
        team.token_active = False
        context = make_context()
        team_repository.find_by_invite_token.return_value = team

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_team_not_draft(self):
        (adapter, team_repository, *_rest) = make_adapter()

        team = make_draft_team()
        team.status = TeamStatus.SUBMITTED
        context = make_context()
        team_repository.find_by_invite_token.return_value = team

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_closed(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        season.status = SeasonStatus.REGISTRATION_CLOSED
        team = make_draft_team(season_id=season.id)
        context = make_context()

        team_repository.find_by_invite_token.return_value = team
        season_repository.get.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_user_already_member(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        team = make_draft_team(season_id=season.id)
        requesting_user_id = uuid4()
        context = make_context(requesting_user_id=requesting_user_id)

        team_repository.find_by_invite_token.return_value = team
        season_repository.get.return_value = season
        team_member_repository.find_members_by_team_id.return_value = [
            TeamMember(
                team_id=team.id,
                user_id=requesting_user_id,
                role=TeamMemberRole.MEMBER,
            )
        ]

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_team_is_full(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        team = make_draft_team(season_id=season.id)
        context = make_context()

        team_repository.find_by_invite_token.return_value = team
        season_repository.get.return_value = season
        team_member_repository.find_members_by_team_id.return_value = [
            TeamMember(team_id=team.id, user_id=uuid4(), role=TeamMemberRole.OWNER)
            for _ in range(2)
        ]
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=1, max_members=2
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_user_in_another_team_same_modality(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
        ) = make_adapter()

        season = make_open_season()
        team = make_draft_team(season_id=season.id)
        requesting_user_id = uuid4()
        context = make_context(requesting_user_id=requesting_user_id)

        other_team = Team(
            id=uuid4(), season_id=season.id, modality_id=team.modality_id
        )

        setup_happy_path(
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            modality_repository,
            team,
            season,
            requesting_user_id,
            other_teams=[other_team],
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.save.assert_not_awaited()

    async def test_blocks_when_invite_token_missing(self):
        (adapter, *_rest) = make_adapter()

        context = Context()
        context.put_property("requesting_user_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_requesting_user_missing(self):
        (adapter, *_rest) = make_adapter()

        context = Context()
        context.put_property("invite_token", "abc123")

        with pytest.raises(BusinessException):
            await adapter.execute(context)
