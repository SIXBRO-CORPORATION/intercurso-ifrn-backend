from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.remove_member_adapter import RemoveMemberAdapter
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
    adapter = RemoveMemberAdapter(
        team_repository, team_member_repository, user_repository, audit_logger
    )
    return adapter, team_repository, team_member_repository, user_repository, audit_logger


def make_context(team_id, target_user_id, requesting_user_id):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("target_user_id", target_user_id)
    context.put_property("requesting_user_id", requesting_user_id)
    return context


@pytest.mark.unit
class TestRemoveMemberAdapter:
    async def test_owner_removes_member_in_draft(self):
        adapter, team_repository, team_member_repository, user_repository, audit_logger = (
            make_adapter()
        )

        owner_id = uuid4()
        target_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )
        member = TeamMember(id=uuid4(), team_id=team.id, user_id=target_user_id)
        owner_user = User(id=owner_id, role=UserRole.USER, atleta=True)
        target_user = User(id=target_user_id, role=UserRole.USER, atleta=True)

        team_repository.get.return_value = team
        user_repository.get.side_effect = lambda user_id: (
            owner_user if user_id == owner_id else target_user
        )
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_repository.find_teams_by_user_id.return_value = []

        context = make_context(team.id, target_user_id, owner_id)

        result = await adapter.execute(context)

        assert result.id == member.id
        team_member_repository.delete.assert_awaited_once_with(member.id)
        assert context.get_property("administrative_operation", bool) is False
        audit_logger.log.assert_awaited_once()
        audit_kwargs = audit_logger.log.await_args.kwargs
        assert audit_kwargs["action"] == AuditAction.TEAM_MEMBER_REMOVED
        assert audit_kwargs["actor_id"] == owner_id

    async def test_monitor_removes_member_regardless_of_team_status(self):
        adapter, team_repository, team_member_repository, user_repository, audit_logger = (
            make_adapter()
        )

        owner_id = uuid4()
        monitor_id = uuid4()
        target_user_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            status=TeamStatus.APPROVED,
        )
        member = TeamMember(id=uuid4(), team_id=team.id, user_id=target_user_id)
        monitor_user = User(id=monitor_id, role=UserRole.MONITOR)
        target_user = User(id=target_user_id, role=UserRole.USER, atleta=True)

        team_repository.get.return_value = team
        user_repository.get.side_effect = lambda user_id: (
            monitor_user if user_id == monitor_id else target_user
        )
        team_member_repository.find_members_by_team_id.return_value = [member]
        team_repository.find_teams_by_user_id.return_value = []

        context = make_context(team.id, target_user_id, monitor_id)

        result = await adapter.execute(context)

        assert result.id == member.id
        assert context.get_property("administrative_operation", bool) is True
        audit_logger.log.assert_awaited_once()
        assert (
            audit_logger.log.await_args.kwargs["action"]
            == AuditAction.TEAM_MEMBER_REMOVED
        )

    async def test_blocks_when_non_owner_non_monitor_tries_to_remove(self):
        adapter, team_repository, team_member_repository, user_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        requesting_user_id = uuid4()
        target_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = User(
            id=requesting_user_id, role=UserRole.USER
        )

        context = make_context(team.id, target_user_id, requesting_user_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()

    async def test_blocks_when_team_not_in_draft_for_owner(self):
        adapter, team_repository, team_member_repository, user_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        target_user_id = uuid4()
        team = Team(
            id=uuid4(),
            name="Turma A",
            owner_id=owner_id,
            status=TeamStatus.SUBMITTED,
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = User(id=owner_id, role=UserRole.USER)

        context = make_context(team.id, target_user_id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()

    async def test_blocks_removing_team_owner(self):
        adapter, team_repository, team_member_repository, user_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = User(id=owner_id, role=UserRole.USER)

        context = make_context(team.id, owner_id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()

    async def test_blocks_when_team_not_found(self):
        adapter, team_repository, *_ = make_adapter()
        team_repository.get.return_value = None

        context = make_context(uuid4(), uuid4(), uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_target_is_not_a_member(self):
        adapter, team_repository, team_member_repository, user_repository, *_ = (
            make_adapter()
        )

        owner_id = uuid4()
        target_user_id = uuid4()
        team = Team(
            id=uuid4(), name="Turma A", owner_id=owner_id, status=TeamStatus.DRAFT
        )

        team_repository.get.return_value = team
        user_repository.get.return_value = User(id=owner_id, role=UserRole.USER)
        team_member_repository.find_members_by_team_id.return_value = []

        context = make_context(team.id, target_user_id, owner_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_member_repository.delete.assert_not_awaited()