from typing import List, Optional, Tuple

from domain.match.match import Match
from domain.match.match_event import MatchEvent
from domain.match.match_set import MatchSet
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User
from web.models.response.match_management_response import (
    MatchManagementResponse,
    MatchModalityConfigurationResponse,
    MatchPlayerResponse,
    MatchSetResponse,
    MatchTeamResponse,
    MatchTimelineEventResponse,
)


class MatchModelMapper:
    def _to_team_response(
        self, team: Team, score: int, sets_won: Optional[int] = None
    ) -> MatchTeamResponse:
        return MatchTeamResponse(
            team_id=team.id,
            name=team.name,
            photo=team.photo,
            score=score,
            sets_won=sets_won,
        )

    def _to_players_response(
        self, players: List[Tuple[TeamMember, User]]
    ) -> List[MatchPlayerResponse]:
        return [
            MatchPlayerResponse(
                user_id=user.id,
                name=user.name,
                matricula=user.matricula,
                role=member.role.value if member.role else "",
            )
            for member, user in players
        ]

    def _to_modality_configuration_response(
        self,
        modality_configuration: Optional[ModalityConfiguration],
        volleyball_configuration: Optional[VolleyballModalityConfiguration] = None,
    ) -> Optional[MatchModalityConfigurationResponse]:
        if modality_configuration is None:
            return None

        return MatchModalityConfigurationResponse(
            num_periods=modality_configuration.num_periods,
            period_duration_minutes=modality_configuration.period_durations_minutes,
            score_type=(
                modality_configuration.score_type.value
                if modality_configuration.score_type
                else None
            ),
            has_third_place_match=modality_configuration.has_third_place_match,
            points_per_set=(
                volleyball_configuration.points_per_set
                if volleyball_configuration
                else None
            ),
            final_set_points=(
                volleyball_configuration.final_set_points
                if volleyball_configuration
                else None
            ),
            sets_to_win=(
                volleyball_configuration.sets_to_win
                if volleyball_configuration
                else None
            ),
        )

    def _to_timeline_response(
        self, events: List[MatchEvent]
    ) -> List[MatchTimelineEventResponse]:
        return [
            MatchTimelineEventResponse(
                event_id=event.id,
                event_type=event.event_type.value if event.event_type else "",
                clock_seconds=event.clock_seconds,
                team_id=event.team_id,
                player_id=event.player_id,
                created_at=event.created_at,
                metadata=event.metadata_json,
            )
            for event in events
        ]

    def _to_sets_response(
        self, match_sets: List[MatchSet]
    ) -> List[MatchSetResponse]:
        return [
            MatchSetResponse(
                set_number=match_set.set_number,
                team1_points=match_set.team1_points,
                team2_points=match_set.team2_points,
                winner_team_id=match_set.winner_team_id,
            )
            for match_set in match_sets
        ]

    def to_management_response(
        self,
        match: Match,
        team1: Team,
        team2: Team,
        team1_players: List[Tuple[TeamMember, User]],
        team2_players: List[Tuple[TeamMember, User]],
        modality: Optional[Modality],
        modality_configuration: Optional[ModalityConfiguration],
        timeline_events: List[MatchEvent],
        volleyball_configuration: Optional[VolleyballModalityConfiguration] = None,
        match_sets: Optional[List[MatchSet]] = None,
        match_point_reached: Optional[bool] = None,
    ) -> MatchManagementResponse:
        match_sets = match_sets or []

        return MatchManagementResponse(
            match_id=match.id,
            bracket_id=match.bracket_id,
            modality_id=modality.id if modality else None,
            modality_name=modality.name if modality else None,
            match_type=match.match_type.value,
            match_category=match.match_category.value,
            status=match.status.value,
            scheduled_date=match.scheduled_date,
            started_at=match.started_at,
            monitor_id=match.monitor_id,
            team1=self._to_team_response(
                team1, match.team1_score, match.team1_sets_won
            ),
            team2=self._to_team_response(
                team2, match.team2_score, match.team2_sets_won
            ),
            team1_players=self._to_players_response(team1_players),
            team2_players=self._to_players_response(team2_players),
            clock_seconds=match.clock_seconds,
            clock_running=match.clock_running,
            current_period=match.current_period,
            modality_configuration=self._to_modality_configuration_response(
                modality_configuration, volleyball_configuration
            ),
            timeline=self._to_timeline_response(timeline_events),
            sets=self._to_sets_response(match_sets),
            metadata=match.metadata_json,
            match_point_reached=match_point_reached,
        )
