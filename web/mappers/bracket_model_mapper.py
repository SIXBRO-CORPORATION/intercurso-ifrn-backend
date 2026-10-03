from typing import Dict, List, Optional, Tuple
from uuid import UUID

from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.match.match import Match
from web.models.response.bracket.bracket_config_suggestion_response import (
    BracketConfigSuggestionResponse,
)
from web.models.response.bracket.bracket_detail_response import (
    BracketDetailResponse,
    BracketGroupResponse,
    BracketGroupTeamResponse,
)
from web.models.response.bracket.bracket_match_response import BracketMatchResponse
from web.models.response.bracket.bracket_response import BracketResponse
from web.models.response.bracket.bracket_summary_response import BracketSummaryResponse
from web.models.response.match.match_response import MatchResponse


class BracketModelMapper:
    def to_config_suggestion_response(
        self,
        modality_id,
        modality_format,
        team_count: int,
        byes_estimated: int,
        suggested_configuration: dict,
    ) -> BracketConfigSuggestionResponse:
        return BracketConfigSuggestionResponse(
            modality_id=modality_id,
            format=modality_format.value,
            team_count=team_count,
            byes_estimated=byes_estimated,
            suggested_configuration=suggested_configuration,
        )

    def to_bracket_response(
        self,
        bracket: Bracket,
        teams_count: int,
        groups_created: int,
        matches_created: int,
        byes_created: int,
        season_transitioned_to_in_progress: bool = False,
    ) -> BracketResponse:
        return BracketResponse(
            bracket_id=bracket.id,
            season_id=bracket.season_id,
            modality_id=bracket.modality_id,
            format=bracket.format.value,
            configuration=bracket.configuration,
            status=bracket.status.value,
            teams_count=teams_count,
            groups_created=groups_created,
            matches_created=matches_created,
            byes_created=byes_created,
            season_transitioned_to_in_progress=season_transitioned_to_in_progress,
        )

    def to_match_response(self, match: Match) -> MatchResponse:
        return MatchResponse(
            match_id=match.id,
            bracket_id=match.bracket_id,
            team1_id=match.team1_id,
            team2_id=match.team2_id,
            scheduled_date=match.scheduled_date,
            status=match.status.value,
            match_type=match.match_type.value,
            match_category=match.match_category.value,
        )

    def to_bracket_summary_response(
        self,
        bracket: Bracket,
        modality_name: Optional[str],
        stats: dict,
    ) -> BracketSummaryResponse:
        return BracketSummaryResponse(
            bracket_id=bracket.id,
            season_id=bracket.season_id,
            modality_id=bracket.modality_id,
            modality_name=modality_name,
            format=bracket.format.value,
            status=bracket.status.value,
            total_matches=stats.get("total_matches", 0),
            started_matches=stats.get("started_matches", 0),
            finished_matches=stats.get("finished_matches", 0),
            available_actions=stats.get("available_actions", []),
        )

    def to_bracket_detail_response(
        self,
        bracket: Bracket,
        modality_name: Optional[str],
        stats: dict,
        groups: List[Tuple[BracketGroup, List[BracketGroupTeam]]],
        matches: List[Match],
        team_names: Dict[UUID, str],
    ) -> BracketDetailResponse:
        group_names = {group.id: group.name for group, _ in groups}
        summary = self.to_bracket_summary_response(bracket, modality_name, stats)
        return BracketDetailResponse(
            **summary.model_dump(),
            configuration=bracket.configuration or {},
            groups=[
                self._to_group_response(group, group_teams, team_names)
                for group, group_teams in groups
            ],
            matches=[
                self.to_bracket_match_response(match, team_names, group_names)
                for match in matches
            ],
        )

    def to_bracket_match_response(
        self,
        match: Match,
        team_names: Dict[UUID, str],
        group_names: Dict[UUID, str],
    ) -> BracketMatchResponse:
        return BracketMatchResponse(
            match_id=match.id,
            bracket_id=match.bracket_id,
            group_name=group_names.get(match.bracket_group_id),
            team1_id=match.team1_id,
            team1_name=team_names.get(match.team1_id),
            team2_id=match.team2_id,
            team2_name=team_names.get(match.team2_id),
            scheduled_date=match.scheduled_date,
            match_type=match.match_type.value,
            match_category=match.match_category.value,
            status=match.status.value,
        )

    def _to_group_response(
        self,
        group: BracketGroup,
        group_teams: List[BracketGroupTeam],
        team_names: Dict[UUID, str],
    ) -> BracketGroupResponse:
        return BracketGroupResponse(
            group_id=group.id,
            name=group.name,
            display_order=group.display_order,
            teams=[
                BracketGroupTeamResponse(
                    team_id=group_team.team_id,
                    team_name=team_names.get(group_team.team_id),
                    points=group_team.points or 0,
                    wins=group_team.wins or 0,
                    draws=group_team.draws or 0,
                    losses=group_team.losses or 0,
                    goals_for=group_team.goals_for or 0,
                    goals_against=group_team.goals_against or 0,
                    goals_difference=group_team.goals_difference or 0,
                )
                for group_team in group_teams
            ],
        )
