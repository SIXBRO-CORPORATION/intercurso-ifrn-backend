from typing import Dict, Optional, Sequence
from uuid import UUID

from core.messaging.team_notification_port import TeamNotificationPort
from domain.team.team import Team
from messaging.services.personal_notifier import PersonalNotifier
from messaging.team_notification_content import (
    captain_selected_content,
    donation_confirmed_content,
    member_joined_content,
    member_left_content,
    member_removed_content,
    team_approved_content,
    team_rejected_content,
)


class TeamNotificationNotifier(TeamNotificationPort):

    def __init__(self, personal_notifier: PersonalNotifier):
        self._personal_notifier = personal_notifier

    async def team_approved(self, team: Team, member_user_ids: Sequence[UUID]) -> None:
        title, body = team_approved_content(team.name)
        await self._notify(member_user_ids, title, body, team, "team_approved")

    async def team_rejected(
        self, team: Team, member_user_ids: Sequence[UUID], reason: str
    ) -> None:
        title, body = team_rejected_content(team.name, reason)
        await self._notify(member_user_ids, title, body, team, "team_rejected")

    async def member_removed(self, team: Team, user_id: UUID) -> None:
        title, body = member_removed_content(team.name)
        await self._notify([user_id], title, body, team, "member_removed")

    async def captain_selected(self, team: Team, user_id: UUID) -> None:
        title, body = captain_selected_content(team.name)
        await self._notify([user_id], title, body, team, "captain_selected")

    async def donation_confirmed(self, team: Team, user_id: UUID) -> None:
        title, body = donation_confirmed_content(team.name)
        await self._notify([user_id], title, body, team, "donation_confirmed")

    async def member_joined(self, team: Team, member_name: str) -> None:
        title, body = member_joined_content(member_name, team.name)
        await self._notify([team.owner_id], title, body, team, "member_joined")

    async def member_left(self, team: Team, member_name: str) -> None:
        title, body = member_left_content(member_name, team.name)
        await self._notify([team.owner_id], title, body, team, "member_left")

    async def _notify(
        self,
        user_ids: Sequence[Optional[UUID]],
        title: str,
        body: str,
        team: Team,
        event: str,
    ) -> None:
        data: Dict[str, str] = {
            "event": event,
            "team_id": str(team.id),
        }
        await self._personal_notifier.notify_users(user_ids, title, body, data)
