from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.delete_team_adapter import DeleteTeamAdapter
from business.team.list_teams_adapter import ListTeamsAdapter
from business.team.regenerate_invite_adapter import RegenerateInviteAdapter
from business.team.reject_team_adapter import RejectTeamAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.user.user import User


def make_context(**props):
    context = Context()
    for key, value in props.items():
        context.put_property(key, value)
    return context


@pytest.mark.unit
class TestDeleteTeamAdapter:
    async def test_owner_deletes_draft_team_and_resets_is_athlete(self):
        team_repository, member_repository, user_repository, audit = (
            AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
        )
        owner_id = uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT)
        owner = User(id=owner_id, role=UserRole.USER, atleta=True)

        team_repository.get.return_value = team
        member_repository.find_members_by_team_id.return_value = []
        user_repository.get.return_value = owner
        team_repository.exists_by_user_id.return_value = False

        adapter = DeleteTeamAdapter(team_repository, member_repository, user_repository, audit)
        await adapter.execute(make_context(team_id=team.id, requesting_user_id=owner_id))

        saved = team_repository.save.await_args.args[0]
        assert saved.deleted_at is not None
        assert audit.log.await_args.kwargs["action"] == AuditAction.TEAM_DELETED

    async def test_blocks_when_not_owner(self):
        team_repository = AsyncMock()
        team = Team(id=uuid4(), owner_id=uuid4(), status=TeamStatus.DRAFT)
        team_repository.get.return_value = team

        adapter = DeleteTeamAdapter(team_repository, AsyncMock(), AsyncMock(), AsyncMock())
        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team_id=team.id, requesting_user_id=uuid4()))

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_not_draft(self):
        team_repository = AsyncMock()
        owner_id = uuid4()
        team = Team(id=uuid4(), owner_id=owner_id, status=TeamStatus.SUBMITTED)
        team_repository.get.return_value = team

        adapter = DeleteTeamAdapter(team_repository, AsyncMock(), AsyncMock(), AsyncMock())
        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team_id=team.id, requesting_user_id=owner_id))

        team_repository.save.assert_not_awaited()


@pytest.mark.unit
class TestRejectTeamAdapter:
    async def test_reject_returns_team_to_draft_with_reason(self):
        team_repository, audit = AsyncMock(), AsyncMock()
        monitor_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=uuid4(),
            status=TeamStatus.SUBMITTED, token_active=False,
            submmited_at=datetime.now(),
        )
        team_repository.get.return_value = team
        team_repository.save.side_effect = lambda t: t

        adapter = RejectTeamAdapter(team_repository, audit)
        result = await adapter.execute(make_context(
            team_id=team.id, rejection_reason="  Falta foto  ", rejected_by_user_id=monitor_id,
        ))

        assert result.status == TeamStatus.DRAFT
        assert result.rejection_reason == "Falta foto"
        assert result.rejected_by == monitor_id
        assert result.rejected_at is not None
        assert result.token_active is True
        assert result.submmited_at is None
        assert audit.log.await_args.kwargs["action"] == AuditAction.TEAM_REJECTED

    async def test_blocks_empty_reason(self):
        adapter = RejectTeamAdapter(AsyncMock(), AsyncMock())
        with pytest.raises(BusinessException):
            await adapter.execute(make_context(
                team_id=uuid4(), rejection_reason="   ", rejected_by_user_id=uuid4(),
            ))

    async def test_blocks_when_not_submitted(self):
        team_repository = AsyncMock()
        team = Team(id=uuid4(), status=TeamStatus.DRAFT)
        team_repository.get.return_value = team

        adapter = RejectTeamAdapter(team_repository, AsyncMock())
        with pytest.raises(BusinessException):
            await adapter.execute(make_context(
                team_id=team.id, rejection_reason="motivo", rejected_by_user_id=uuid4(),
            ))

        team_repository.save.assert_not_awaited()


@pytest.mark.unit
class TestRegenerateInviteAdapter:
    async def test_owner_gets_new_token_and_old_one_is_replaced(self):
        team_repository = AsyncMock()
        owner_id = uuid4()
        team = Team(
            id=uuid4(), owner_id=owner_id, status=TeamStatus.DRAFT,
            invite_token="old-token", token_active=False,
        )
        team_repository.get.return_value = team
        team_repository.save.side_effect = lambda t: t

        adapter = RegenerateInviteAdapter(team_repository, AsyncMock())
        result = await adapter.execute(make_context(team_id=team.id, requesting_user_id=owner_id))

        assert result.invite_token != "old-token"
        assert result.token_active is True

    async def test_blocks_non_owner(self):
        team_repository = AsyncMock()
        team = Team(id=uuid4(), owner_id=uuid4(), status=TeamStatus.DRAFT, invite_token="t")
        team_repository.get.return_value = team

        adapter = RegenerateInviteAdapter(team_repository, AsyncMock())
        with pytest.raises(BusinessException):
            await adapter.execute(make_context(team_id=team.id, requesting_user_id=uuid4()))

        team_repository.save.assert_not_awaited()


@pytest.mark.unit
class TestListTeamsStudentFilters:
    async def test_season_and_status_are_pushed_down_to_the_query(self):
        """Filtro roda no SQL (sem puxar todos os times e filtrar em memória)."""
        team_repository = AsyncMock()
        member_repository, user_repository, modality_repository = AsyncMock(), AsyncMock(), AsyncMock()
        season_id, requesting_user_id = uuid4(), uuid4()
        expected = [Team(id=uuid4(), season_id=season_id, status=TeamStatus.DRAFT)]
        team_repository.find_teams_by_user_id_with_filters.return_value = expected
        modality_repository.find_by_ids.return_value = []
        user_repository.find_by_ids.return_value = []
        member_repository.count_by_teams.return_value = {}
        member_repository.count_pending_donations_by_teams.return_value = {}

        adapter = ListTeamsAdapter(team_repository, member_repository, user_repository, modality_repository)
        context = make_context(
            requesting_user_id=requesting_user_id, requesting_user_role=UserRole.USER,
            season_id=season_id, status=TeamStatus.DRAFT,
        )
        result = await adapter.execute(context)

        assert result == expected
        team_repository.find_teams_by_user_id_with_filters.assert_awaited_once_with(
            requesting_user_id, season_id, TeamStatus.DRAFT
        )
        team_repository.find_teams_by_user_id.assert_not_called()
