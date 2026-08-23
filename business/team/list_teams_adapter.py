from typing import List
from uuid import UUID

from core.business.team.list_teams_port import ListTeamsPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class ListTeamsAdapter(ListTeamsPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> List[Team]:
        requesting_user_id = context.get_property("requesting_user_id", UUID)
        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        requesting_role = context.get_property("requesting_user_role", UserRole)
        is_monitor_operation = requesting_role in (UserRole.MONITOR, UserRole.ADMIN)

        status_filter = context.get_property("status", TeamStatus)
        season_id_filter = context.get_property("season_id", UUID)

        if is_monitor_operation:
            teams = await self._find_teams_for_monitor(status_filter, season_id_filter)
        else:
            teams = await self.team_repository.find_teams_by_user_id(
                requesting_user_id
            )

        team_extra_info = {}
        for team in teams:
            team_extra_info[team.id] = await self._build_extra_info(team)

        context.put_property("team_extra_info", team_extra_info)

        return teams

    async def _find_teams_for_monitor(
        self, status_filter, season_id_filter
    ) -> List[Team]:
        if status_filter is not None:
            teams = await self.team_repository.find_teams_by_status(status_filter)
            if season_id_filter is not None:
                teams = [t for t in teams if t.season_id == season_id_filter]
            return teams

        if season_id_filter is not None:
            return await self.team_repository.find_by_season_id(season_id_filter)

        return await self.team_repository.find_all()

    async def _build_extra_info(self, team: Team) -> dict:
        modality = await self.modality_repository.get(team.modality_id)
        owner_user = (
            await self.user_repository.get(team.owner_id) if team.owner_id else None
        )
        members_count = await self.team_member_repository.count_by_team(team.id)
        pending_donations = (
            await self.team_member_repository.count_pending_donations_by_team(
                team.id
            )
        )

        return {
            "modality_name": modality.name if modality else None,
            "owner_name": owner_user.name if owner_user else None,
            "members_count": members_count,
            "donations_confirmed": members_count - pending_donations,
            "donations_total": members_count,
        }
