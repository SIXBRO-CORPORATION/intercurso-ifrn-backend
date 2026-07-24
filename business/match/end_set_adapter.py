from datetime import datetime
from uuid import UUID

from business.match._shared import (
    load_management_context,
    load_modality_configuration,
    validate_match_in_progress,
)
from core.business.match.end_set_port import EndSetPort
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
from domain.match import Match
from domain.match.match_event import MatchEvent


class EndSetAdapter(EndSetPort):
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
        DEFAULT_POINTS_PER_SET = 25
        DEFAULT_FINAL_SET_POINTS = 15
        DEFAULT_SETS_TO_WIN = 2

        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )

        _, modality_configuration = await load_modality_configuration(
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            match.bracket_id,
        )
        if (
            modality_configuration is None
            or modality_configuration.score_type != ScoreType.SETS
        ):
            raise BusinessException(
                "Esta modalidade não usa sistema de sets (vôlei)"
            )

        config_metadata = modality_configuration.metadata or {}
        points_per_set = config_metadata.get("points_per_set", DEFAULT_POINTS_PER_SET)
        final_set_points = config_metadata.get(
            "final_set_points", DEFAULT_FINAL_SET_POINTS
        )
        sets_to_win = config_metadata.get("sets_to_win", DEFAULT_SETS_TO_WIN)

        metadata = dict(match.metadata_json or {})
        current_set_score = dict(
            metadata.get("current_set_score") or {"team1": 0, "team2": 0}
        )
        current_set_number = metadata.get("current_set_number", 1)
        sets = list(metadata.get("sets") or [])
        sets_won = dict(metadata.get("sets_won") or {"team1": 0, "team2": 0})

        team1_points = current_set_score.get("team1", 0)
        team2_points = current_set_score.get("team2", 0)

        is_final_set = current_set_number == (2 * sets_to_win - 1)
        points_required = final_set_points if is_final_set else points_per_set

        winner_key = None
        if (
            team1_points >= points_required
            and team1_points - team2_points >= 2
        ):
            winner_key = "team1"
        elif (
            team2_points >= points_required
            and team2_points - team1_points >= 2
        ):
            winner_key = "team2"

        if winner_key is None:
            raise BusinessException(
                "Pontuação do set ainda não atinge os critérios de fim de set "
                f"({points_required} pontos com diferença mínima de 2). "
                f"Placar atual: {team1_points}x{team2_points}"
            )

        winner_team_id = match.team1_id if winner_key == "team1" else match.team2_id

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        sets.append(
            {
                "set_number": current_set_number,
                "score": f"{team1_points}x{team2_points}",
                "winner_team_id": str(winner_team_id),
            }
        )
        sets_won[winner_key] = sets_won.get(winner_key, 0) + 1

        metadata["sets"] = sets
        metadata["sets_won"] = sets_won
        metadata["current_set_score"] = {"team1": 0, "team2": 0}
        metadata["current_set_number"] = current_set_number + 1
        match.metadata_json = metadata

        match.sync_clock(now)
        saved_match = await self.match_repository.save(match)

        set_end_event = MatchEvent(
            match_id=match_id,
            team_id=winner_team_id,
            event_type=EventType.SET_END,
            clock_seconds=clock_seconds,
            metadata_json={
                "set_number": current_set_number,
                "score": f"{team1_points}x{team2_points}",
                "winner_team_id": str(winner_team_id),
                "sets_won": sets_won,
            },
        )
        await self.match_event_repository.save(set_end_event)

        context.put_property(
            "match_point_reached", sets_won.get(winner_key, 0) >= sets_to_win
        )

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
