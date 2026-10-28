from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from business.team.join_team_via_invite_adapter import JoinTeamViaInviteAdapter
from business.team.leave_team_adapter import LeaveTeamAdapter
from business.team.reject_team_adapter import RejectTeamAdapter
from business.team.remove_member_adapter import RemoveMemberAdapter
from business.team.select_captain_adapter import SelectCaptainAdapter
from core.context import Context
from domain.enums.donation_status import DonationStatus
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User


def ctx(**props) -> Context:
    context = Context()
    for key, value in props.items():
        context.put_property(key, value)
    return context


def member(team_id, user_id) -> TeamMember:
    return TeamMember(
        team_id=team_id, user_id=user_id, role=TeamMemberRole.MEMBER,
        donation_status=DonationStatus.PENDING_DONATION,
    )


@pytest.mark.unit
class TestTeamNotifications:

    @pytest.mark.asyncio
    async def test_reject_notifies_every_member_with_reason(self):
        team_repository, audit = AsyncMock(), AsyncMock()
        team_member_repository = AsyncMock()
        notification = AsyncMock()
        team = Team(id=uuid4(), name="Turma A", owner_id=uuid4(),
                    status=TeamStatus.SUBMITTED)
        members = [member(team.id, uuid4()), member(team.id, uuid4())]
        team_repository.get.return_value = team
        team_repository.save.side_effect = lambda t: t
        team_member_repository.find_members_by_team_id.return_value = members

        adapter = RejectTeamAdapter(team_repository, audit, team_member_repository,
                                    notification)
        await adapter.execute(ctx(team_id=team.id, rejection_reason="Falta foto",
                                  rejected_by_user_id=uuid4()))

        sent_team, sent_ids, reason = notification.team_rejected.await_args.args
        assert sent_team.id == team.id
        assert sent_ids == [m.user_id for m in members]
        assert reason == "Falta foto"

    @pytest.mark.asyncio
    async def test_reject_blocked_does_not_notify(self):
        team_repository = AsyncMock()
        notification = AsyncMock()
        team_repository.get.return_value = Team(id=uuid4(), status=TeamStatus.DRAFT)

        adapter = RejectTeamAdapter(team_repository, AsyncMock(), AsyncMock(),
                                    notification)
        with pytest.raises(BusinessException):
            await adapter.execute(ctx(team_id=uuid4(), rejection_reason="x",
                                      rejected_by_user_id=uuid4()))
        notification.team_rejected.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_approve_notifies_every_member(self):
        team_repository = AsyncMock()
        team_member_repository = AsyncMock()
        notification = AsyncMock()
        team = Team(id=uuid4(), name="Turma A", status=TeamStatus.SUBMITTED)
        members = [member(team.id, uuid4()), member(team.id, uuid4())]
        team_repository.get.return_value = team
        team_repository.save.side_effect = lambda t: t
        team_member_repository.find_members_by_team_id.return_value = members

        adapter = ApproveTeamAdapter(team_repository, team_member_repository,
                                     AsyncMock(), AsyncMock(), AsyncMock(), notification)
        with patch("business.team.approve_team_adapter.evaluate_approve_eligibility",
                   return_value=(True, None)):
            await adapter.execute(ctx(team_id=team.id, approved_by_user_id=uuid4()))

        sent_team, sent_ids = notification.team_approved.await_args.args
        assert sent_team.status == TeamStatus.APPROVED
        assert sent_ids == [m.user_id for m in members]

    @pytest.mark.asyncio
    async def test_remove_member_notifies_removed_user(self):
        team_repository, team_member_repository = AsyncMock(), AsyncMock()
        user_repository, notification = AsyncMock(), AsyncMock()
        owner_id, target_id = uuid4(), uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=owner_id,
                    status=TeamStatus.DRAFT)
        team_repository.get.return_value = team
        team_repository.exists_by_user_id.return_value = False
        team_member_repository.find_by_team_and_user.return_value = member(team.id, target_id)
        user_repository.get.side_effect = lambda uid: User(
            id=uid, name="X", atleta=False)

        adapter = RemoveMemberAdapter(team_repository, team_member_repository,
                                      user_repository, AsyncMock(), notification)
        await adapter.execute(ctx(team_id=team.id, target_user_id=target_id,
                                  requesting_user_id=owner_id))

        notification.member_removed.assert_awaited_once_with(team, target_id)

    @pytest.mark.asyncio
    async def test_remove_member_blocked_does_not_notify(self):
        team_repository, notification = AsyncMock(), AsyncMock()
        owner_id = uuid4()
        team_repository.get.return_value = Team(id=uuid4(), owner_id=owner_id,
                                                status=TeamStatus.APPROVED)
        user_repository = AsyncMock()
        user_repository.get.return_value = User(id=owner_id, name="Dono")

        adapter = RemoveMemberAdapter(team_repository, AsyncMock(), user_repository,
                                      AsyncMock(), notification)
        with pytest.raises(BusinessException):
            await adapter.execute(ctx(team_id=uuid4(), target_user_id=uuid4(),
                                      requesting_user_id=owner_id))
        notification.member_removed.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_select_captain_notifies_new_captain(self):
        team_repository, team_member_repository = AsyncMock(), AsyncMock()
        user_repository, notification = AsyncMock(), AsyncMock()
        owner_id, captain_id = uuid4(), uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=owner_id,
                    status=TeamStatus.DRAFT)
        team_repository.get.return_value = team
        team_repository.save.side_effect = lambda t: t
        team_member_repository.find_by_team_and_user.return_value = member(team.id, captain_id)
        user_repository.get.return_value = User(id=owner_id, name="Dono")

        adapter = SelectCaptainAdapter(team_repository, team_member_repository,
                                       user_repository, AsyncMock(), notification)
        await adapter.execute(ctx(team_id=team.id, target_user_id=captain_id,
                                  requesting_user_id=owner_id))

        notification.captain_selected.assert_awaited_once()
        sent_team, sent_user = notification.captain_selected.await_args.args
        assert sent_user == captain_id
        assert sent_team.captain_id == captain_id

    @pytest.mark.asyncio
    async def test_confirm_donation_notifies_member(self):
        team_repository, team_member_repository = AsyncMock(), AsyncMock()
        user_repository, notification = AsyncMock(), AsyncMock()
        target_id = uuid4()
        team = Team(id=uuid4(), name="Turma A", status=TeamStatus.APPROVED)
        team_repository.get.return_value = team
        user_repository.get.return_value = User(id=target_id, name="Ana")
        team_member_repository.find_by_team_and_user.return_value = member(team.id, target_id)
        team_member_repository.save.side_effect = lambda m: m

        adapter = ConfirmDonationAdapter(team_repository, team_member_repository,
                                         user_repository, AsyncMock(), notification)
        await adapter.execute(ctx(team_id=team.id, target_user_id=target_id,
                                  confirmed_by_user_id=uuid4()))

        notification.donation_confirmed.assert_awaited_once_with(team, target_id)

    @pytest.mark.asyncio
    async def test_join_notifies_owner_with_joining_member_name(self):
        team_repository, team_member_repository = AsyncMock(), AsyncMock()
        user_repository, season_repository = AsyncMock(), AsyncMock()
        notification = AsyncMock()
        joiner_id = uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=uuid4(), season_id=uuid4(),
                    modality_id=None, status=TeamStatus.DRAFT, token_active=True,
                    invite_token="tok")
        team_repository.find_by_invite_token.return_value = team
        team_repository.exists_by_user_season_and_modality.return_value = False
        season_repository.get.return_value = Season(
            id=team.season_id, status=SeasonStatus.REGISTRATION_OPEN)
        team_member_repository.exists_by_team_and_user.return_value = False
        team_member_repository.save.side_effect = lambda m: m
        user_repository.get.return_value = User(id=joiner_id, name="Maria", atleta=True)

        modality_repository = AsyncMock()
        modality_repository.get.return_value = None  # sem restrições de modalidade

        adapter = JoinTeamViaInviteAdapter(
            team_repository, team_member_repository, user_repository,
            season_repository, modality_repository, AsyncMock(), notification,
        )
        await adapter.execute(ctx(invite_token="tok", requesting_user_id=joiner_id))

        sent_team, sent_name = notification.member_joined.await_args.args
        assert sent_team.id == team.id
        assert sent_name == "Maria"

    @pytest.mark.asyncio
    async def test_join_blocked_does_not_notify(self):
        team_repository, notification = AsyncMock(), AsyncMock()
        team_repository.find_by_invite_token.return_value = None

        adapter = JoinTeamViaInviteAdapter(
            team_repository, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock(),
            AsyncMock(), notification,
        )
        with pytest.raises(BusinessException):
            await adapter.execute(ctx(invite_token="bad", requesting_user_id=uuid4()))
        notification.member_joined.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_leave_notifies_owner_with_leaving_member_name(self):
        team_repository, team_member_repository = AsyncMock(), AsyncMock()
        user_repository, notification = AsyncMock(), AsyncMock()
        leaver_id, owner_id = uuid4(), uuid4()
        team = Team(id=uuid4(), name="Turma A", owner_id=owner_id,
                    status=TeamStatus.DRAFT)
        team_repository.get.return_value = team
        team_repository.exists_by_user_id.return_value = False
        team_member_repository.find_by_team_and_user.return_value = member(team.id, leaver_id)
        user_repository.get.return_value = User(id=leaver_id, name="Ana", atleta=False)

        adapter = LeaveTeamAdapter(team_repository, team_member_repository,
                                   user_repository, AsyncMock(), notification)
        await adapter.execute(ctx(team_id=team.id, requesting_user_id=leaver_id))

        sent_team, sent_name = notification.member_left.await_args.args
        assert sent_team.owner_id == owner_id
        assert sent_name == "Ana"

    @pytest.mark.asyncio
    async def test_leave_blocked_for_owner_does_not_notify(self):
        owner_id = uuid4()
        team_repository, notification = AsyncMock(), AsyncMock()
        team_repository.get.return_value = Team(id=uuid4(), owner_id=owner_id,
                                                status=TeamStatus.DRAFT)

        adapter = LeaveTeamAdapter(team_repository, AsyncMock(), AsyncMock(),
                                   AsyncMock(), notification)
        with pytest.raises(BusinessException):
            await adapter.execute(ctx(team_id=uuid4(), requesting_user_id=owner_id))
        notification.member_left.assert_not_awaited()
