from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.team.team import Team
from messaging.services.team_notification_notifier import TeamNotificationNotifier
from messaging.team_notification_content import (
    DEFAULT_MEMBER_NAME,
    member_joined_content,
    team_rejected_content,
)


def make_notifier():
    personal_notifier = AsyncMock()
    return TeamNotificationNotifier(personal_notifier=personal_notifier), personal_notifier


def make_team() -> Team:
    return Team(id=uuid4(), name="Turma A", owner_id=uuid4())


@pytest.mark.unit
class TestTeamNotificationNotifier:

    @pytest.mark.asyncio
    async def test_rejection_goes_to_all_members_with_reason(self):
        notifier, personal = make_notifier()
        team = make_team()
        members = [uuid4(), uuid4()]

        await notifier.team_rejected(team, members, "Falta foto")

        personal.notify_users.assert_awaited_once()
        args = personal.notify_users.await_args.args
        assert list(args[0]) == members
        assert "Falta foto" in args[2]
        assert args[3] == {"event": "team_rejected", "team_id": str(team.id)}

    @pytest.mark.asyncio
    async def test_join_notifies_only_the_owner(self):
        notifier, personal = make_notifier()
        team = make_team()

        await notifier.member_joined(team, "Maria")

        args = personal.notify_users.await_args.args
        assert list(args[0]) == [team.owner_id]
        assert "Maria" in args[2]

    @pytest.mark.asyncio
    async def test_leave_notifies_only_the_owner(self):
        notifier, personal = make_notifier()
        team = make_team()

        await notifier.member_left(team, "Ana")

        args = personal.notify_users.await_args.args
        assert list(args[0]) == [team.owner_id]
        assert args[3]["event"] == "member_left"

    @pytest.mark.asyncio
    async def test_single_user_events_target_that_user(self):
        notifier, personal = make_notifier()
        team = make_team()
        user_id = uuid4()

        await notifier.member_removed(team, user_id)
        await notifier.captain_selected(team, user_id)
        await notifier.donation_confirmed(team, user_id)

        targets = [call.args[0] for call in personal.notify_users.await_args_list]
        assert targets == [[user_id], [user_id], [user_id]]


@pytest.mark.unit
class TestTeamNotificationContent:

    def test_rejection_content_includes_team_and_reason(self):
        title, body = team_rejected_content("Turma A", "Falta foto")
        assert title
        assert "Turma A" in body and "Falta foto" in body

    def test_member_joined_falls_back_when_name_missing(self):
        _, body = member_joined_content(None, "Turma A")
        assert body.startswith(DEFAULT_MEMBER_NAME)

    def test_member_joined_falls_back_when_name_blank(self):
        _, body = member_joined_content("   ", "Turma A")
        assert body.startswith(DEFAULT_MEMBER_NAME)
