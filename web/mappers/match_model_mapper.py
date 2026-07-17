from typing import List, Optional, Tuple

from domain.match import Match
from domain.match_event import MatchEvent
from domain.modality import Modality
from domain.modality_configuration import ModalityConfiguration
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User
from web.models.response.match_management_response import (
    MatchManagementResponse,
    MatchModalityConfigurationResponse,
    MatchPlayerResponse,
    MatchTeamResponse,
    MatchTimelineEventResponse,
)


class MatchModelMapper:
    def _to_team_response(self, team: Team, score: int) -> MatchTeamResponse:
        return MatchTeamResponse(
            team_id=team.id,
            name=team.name,
            photo=team.photo,
            score=score,
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
        self, modality_configuration: Optional[ModalityConfiguration]
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
            )
            for event in events
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
    ) -> MatchManagementResponse:
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
            team1=self._to_team_response(team1, match.team1_score),
            team2=self._to_team_response(team2, match.team2_score),
            team1_players=self._to_players_response(team1_players),
            team2_players=self._to_players_response(team2_players),
            clock_seconds=match.clock_seconds,
            clock_running=match.clock_running,
            current_period=match.current_period,
            modality_configuration=self._to_modality_configuration_response(
                modality_configuration
            ),
            timeline=self._to_timeline_response(timeline_events),
        )
