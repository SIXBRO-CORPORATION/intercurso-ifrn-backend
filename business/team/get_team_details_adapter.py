from datetime import datetime, timezone
from uuid import UUID

from business.team._shared import evaluate_approve_eligibility, evaluate_submit_eligibility
from core.business.team.get_team_details_port import GetTeamDetailsPort
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import (
    BracketGroupRepositoryPort,
)
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team


class GetTeamDetailsAdapter(GetTeamDetailsPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        season_repository: SeasonRepositoryPort,
        match_repository: MatchRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.modality_repository = modality_repository
        self.season_repository = season_repository
        self.match_repository = match_repository
        self.bracket_group_repository = bracket_group_repository

    async def execute(self, context: Context) -> Team:
        team_id = context.get_property("team_id", UUID)
        requesting_user_id = context.get_property("requesting_user_id", UUID)

        if team_id is None:
            raise BusinessException("Identificador do time é obrigatório")

        if requesting_user_id is None:
            raise BusinessException("Usuário é obrigatório")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        requesting_role = context.get_property("requesting_user_role", UserRole)
        is_monitor_operation = requesting_role in (UserRole.MONITOR, UserRole.ADMIN)

        if is_monitor_operation and team.status == TeamStatus.DRAFT:
            raise BusinessException("Você não tem permissão para visualizar este time")

        if not is_monitor_operation:
            is_member = await self.team_member_repository.exists_by_team_and_user(
                team_id, requesting_user_id
            )
            if not is_member:
                raise BusinessException(
                    "Você não tem permissão para visualizar este time"
                )

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        member_user_ids = [member.user_id for member in members]
        member_users = (
            await self.user_repository.find_by_ids(member_user_ids)
            if member_user_ids
            else []
        )
        member_users_by_id = {user.id: user for user in member_users}

        modality = await self.modality_repository.get(team.modality_id)
        owner_user = member_users_by_id.get(team.owner_id) or (
            await self.user_repository.get(team.owner_id) if team.owner_id else None
        )
        captain_user = (
            member_users_by_id.get(team.captain_id)
            if team.captain_id
            else None
        )
        if team.captain_id and captain_user is None:
            captain_user = await self.user_repository.get(team.captain_id)

        can_submit = False
        submit_blocked_reason = None
        if team.status == TeamStatus.DRAFT:
            active_season = await self.season_repository.find_active_season()
            can_submit, submit_blocked_reason = evaluate_submit_eligibility(
                team,
                members,
                modality,
                active_season,
                member_users,
                datetime.now(timezone.utc),
            )

        can_approve = False
        approve_blocked_reason = None
        if team.status == TeamStatus.SUBMITTED:
            can_approve, approve_blocked_reason = evaluate_approve_eligibility(
                team, members, modality, member_users
            )

        next_match = None
        next_match_group_name = None
        next_match_team1 = None
        next_match_team2 = None
        if team.status == TeamStatus.APPROVED:
            next_match = await self.match_repository.find_next_match_by_team(team_id)
            if next_match is not None:
                if next_match.bracket_group_id is not None:
                    group = await self.bracket_group_repository.get(
                        next_match.bracket_group_id
                    )
                    next_match_group_name = group.name if group else None
                opponent_ids = [
                    t
                    for t in (next_match.team1_id, next_match.team2_id)
                    if t is not None
                ]
                opponent_teams = (
                    await self.team_repository.find_by_ids(opponent_ids)
                    if opponent_ids
                    else []
                )
                teams_by_id = {t.id: t for t in opponent_teams}

                teams_by_id.setdefault(team.id, team)
                next_match_team1 = teams_by_id.get(next_match.team1_id)
                next_match_team2 = teams_by_id.get(next_match.team2_id)

        context.put_property("modality", modality)
        context.put_property("members", members)
        context.put_property("member_users_by_id", member_users_by_id)
        context.put_property("owner_user", owner_user)
        context.put_property("captain_user", captain_user)
        context.put_property("can_submit", can_submit)
        context.put_property("submit_blocked_reason", submit_blocked_reason)
        context.put_property("can_approve", can_approve)
        context.put_property("approve_blocked_reason", approve_blocked_reason)
        context.put_property("next_match", next_match)
        context.put_property("next_match_group_name", next_match_group_name)
        context.put_property("next_match_team1", next_match_team1)
        context.put_property("next_match_team2", next_match_team2)

        return team
