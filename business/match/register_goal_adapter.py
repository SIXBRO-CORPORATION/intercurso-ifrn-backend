from datetime import datetime
from uuid import UUID

from business.match._shared import (
    is_player_expelled,
    load_management_context,
    load_modality_configuration,
    validate_match_in_progress,
    validate_player_in_team,
    validate_team_in_match,
)
from core.business.match.register_goal_port import RegisterGoalPort
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.event_type import EventType
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.match.match_event import MatchEvent


class RegisterGoalAdapter(RegisterGoalPort):
    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        match_event_repository: MatchEventRepositoryPort,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        bracket_repository: BracketRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
    ):
        self.match_repository = match_repository
        self.match_event_repository = match_event_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.bracket_repository = bracket_repository
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)
        team_id = context.get_property("team_id", UUID)
        player_id = context.get_property("player_id", UUID)

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )
        await validate_team_in_match(match, team_id)
        await validate_player_in_team(self.team_member_repository, team_id, player_id)

        if await is_player_expelled(self.match_event_repository, match_id, player_id):
            raise BusinessException("Jogador expulso não pode marcar pontos")

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        _, modality_configuration = await load_modality_configuration(
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            match.bracket_id,
        )
        score_type = (
            modality_configuration.score_type if modality_configuration else None
        )
        event_type = EventType.GOAL if score_type == ScoreType.GOALS else EventType.POINT

        if team_id == match.team1_id:
            match.team1_score = (match.team1_score or 0) + 1
        else:
            match.team2_score = (match.team2_score or 0) + 1

        if score_type == ScoreType.SETS:
            self._update_set_score(match, team_id)

        match.sync_clock(now)
        saved_match = await self.match_repository.save(match)

        goal_event = MatchEvent(
            match_id=match.id,
            team_id=team_id,
            player_id=player_id,
            event_type=event_type,
            clock_seconds=clock_seconds,
        )
        await self.match_event_repository.save(goal_event)

        await load_management_context(
            context,
            saved_match,
            self.team_repository,
            self.team_member_repository,
            self.user_repository,
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            self.match_event_repository,
        )

        return saved_match

    def _update_set_score(self, match: Match, team_id: UUID) -> None:
        metadata = dict(match.metadata_json or {})
        current_set_score = dict(metadata.get("current_set_score") or {"team1": 0, "team2": 0})
        key = "team1" if team_id == match.team1_id else "team2"
        current_set_score[key] = current_set_score.get(key, 0) + 1
        metadata["current_set_score"] = current_set_score
        metadata.setdefault("current_set_number", 1)
        metadata.setdefault("sets", [])
        metadata.setdefault("sets_won", {"team1": 0, "team2": 0})
        match.metadata_json = metadata
