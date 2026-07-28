from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.submit_team_adapter import SubmitTeamAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.donation_status import DonationStatus
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    season_repository = AsyncMock()
    modality_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    adapter = SubmitTeamAdapter(
        team_repository,
        team_member_repository,
        season_repository,
        modality_repository,
        user_repository,
        audit_logger,
    )
    return (
        adapter,
        team_repository,
        team_member_repository,
        season_repository,
        modality_repository,
        user_repository,
        audit_logger,
    )


def make_open_season(team_season_id):
    now = datetime.now(timezone.utc)
    return Season(
        id=team_season_id,
        name="Intercurso 2026",
        status=SeasonStatus.REGISTRATION_OPEN,
        registration_start_date=now - timedelta(days=1),
        registration_end_date=now + timedelta(days=10),
    )


def make_context(team_id, requesting_user_id):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("requesting_user_id", requesting_user_id)
    return context


@pytest.mark.unit
class TestSubmitTeamAdapter:
    async def test_submits_team_successfully(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            season_repository,
            modality_repository,
            user_repository,
            audit_logger,
        ) = make_adapter()

        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            season_id=season_id,
            modality_id=uuid4(),
            status=TeamStatus.DRAFT,
        )
        season = make_open_season(season_id)
        members = [
            TeamMember(
                id=uuid4(),
                team_id=team.id,
                user_id=uuid4(),
                donation_status=DonationStatus.DONATION_CONFIRMED,
            )
            for _ in range(5)
        ]

        team_repository.get.return_value = team
        season_repository.find_active_season.return_value = season
        team_member_repository.find_members_by_team_id.return_value = members
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )
        team_repository.save.side_effect = lambda t: t
        user_repository.get.return_value = User(id=owner_id, role=UserRole.USER)

        context = make_context(team.id, owner_id)

        result = await adapter.execute(context)

        assert result.status == TeamStatus.SUBMITTED
        assert result.token_active is False
        assert result.submmited_at is not None
        assert team_member_repository.save.await_count == len(members)
        audit_logger.log.assert_awaited_once()
        audit_kwargs = audit_logger.log.await_args.kwargs
        assert audit_kwargs["action"] == AuditAction.TEAM_SUBMITTED
        assert audit_kwargs["actor_id"] == owner_id

    async def test_blocks_when_requester_is_not_owner(self):
        adapter, team_repository, *_ = make_adapter()

        owner_id = uuid4()
        requesting_user_id = uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=owner_id)
        team_repository.get.return_value = team

        context = make_context(team.id, requesting_user_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_not_in_draft(self):
        adapter, team_repository, *_ = make_adapter()

        owner_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            status=TeamStatus.SUBMITTED,
        )
        team_repository.get.return_value = team

        context = make_context(team.id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_no_active_season_matches_team_season(self):
        adapter, team_repository, team_member_repository, season_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            season_id=uuid4(),
            status=TeamStatus.DRAFT,
        )
        team_repository.get.return_value = team
        season_repository.find_active_season.return_value = None

        context = make_context(team.id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_not_open(self):
        adapter, team_repository, team_member_repository, season_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            season_id=season_id,
            status=TeamStatus.DRAFT,
        )
        season = make_open_season(season_id)
        season.status = SeasonStatus.REGISTRATION_CLOSED

        team_repository.get.return_value = team
        season_repository.find_active_season.return_value = season

        context = make_context(team.id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_below_minimum_members(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            season_repository,
            modality_repository,
            *_rest,
        ) = make_adapter()

        owner_id = uuid4()
        season_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            season_id=season_id,
            modality_id=uuid4(),
            status=TeamStatus.DRAFT,
        )
        season = make_open_season(season_id)

        team_repository.get.return_value = team
        season_repository.find_active_season.return_value = season
        team_member_repository.find_members_by_team_id.return_value = [
            TeamMember(id=uuid4(), team_id=team.id, user_id=uuid4())
        ]
        modality_repository.get.return_value = Modality(
            id=team.modality_id, name="Futsal", min_members=5, max_members=10
        )

        context = make_context(team.id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, *_ = make_adapter()
        team_repository.get.return_value = None

        context = make_context(uuid4(), uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)