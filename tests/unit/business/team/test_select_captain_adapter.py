from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.leave_team_adapter import LeaveTeamAdapter
from core.context import Context
from domain.enums.audit_action import AuditAction
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    adapter = LeaveTeamAdapter(
        team_repository, team_member_repository, user_repository, audit_logger
    )
    return adapter, team_repository, team_member_repository, user_repository, audit_logger


def make_context(team_id, requesting_user_id):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("requesting_user_id", requesting_user_id)
    return context


@pytest.mark.unit
class TestLeaveTeamAdapter:
    async def test_member_leaves_team_and_deactivates_atleta_flag(self):
        adapter, team_repository, team_member_repository, user_repository, audit_logger = (
            make_adapter()
        )

        owner_id = uuid4()
        requesting_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )
        member = TeamMember(id=uuid4(), team_id=team.id, user_id=requesting_user_id)
        requesting_user = User(id=requesting_user_id, role=UserRole.USER, atleta=True)

        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_repository.find_teams_by_user_id.return_value = []
        user_repository.get.return_value = requesting_user

        context = make_context(team.id, requesting_user_id)

        result = await adapter.execute(context)

        assert result.id == member.id
        team_member_repository.delete.assert_awaited_once_with(member.id)
        user_repository.save.assert_awaited_once()
        assert requesting_user.atleta is False
        audit_logger.log.assert_awaited_once()
        audit_kwargs = audit_logger.log.await_args.kwargs
        assert audit_kwargs["action"] == AuditAction.TEAM_MEMBER_LEFT
        assert audit_kwargs["actor_id"] == requesting_user_id

    async def test_does_not_resave_user_when_still_in_other_team(self):
        adapter, team_repository, team_member_repository, user_repository, audit_logger = (
            make_adapter()
        )

        owner_id = uuid4()
        requesting_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )
        member = TeamMember(id=uuid4(), team_id=team.id, user_id=requesting_user_id)

        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_repository.find_teams_by_user_id.return_value = [Team(id=uuid4())]
        user_repository.get.return_value = User(
            id=requesting_user_id, role=UserRole.USER, atleta=True
        )

        context = make_context(team.id, requesting_user_id)

        await adapter.execute(context)

        user_repository.save.assert_not_awaited()

    async def test_blocks_owner_from_leaving(self):
        adapter, team_repository, team_member_repository, *_ = make_adapter()

        owner_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )
        team_repository.get.return_value = team

        context = make_context(team.id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()

    async def test_blocks_when_team_not_in_draft(self):
        adapter, team_repository, team_member_repository, *_ = make_adapter()

        owner_id = uuid4()
        requesting_user_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            status=TeamStatus.SUBMITTED,
        )
        team_repository.get.return_value = team

        context = make_context(team.id, requesting_user_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, *_ = make_adapter()
        team_repository.get.return_value = None

        context = make_context(uuid4(), uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_requesting_user_is_not_a_member(self):
        adapter, team_repository, team_member_repository, *_ = make_adapter()

        owner_id = uuid4()
        requesting_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )
        team_repository.get.return_value = team
        team_member_repository.find_members_by_team_id.return_value = []

        context = make_context(team.id, requesting_user_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()