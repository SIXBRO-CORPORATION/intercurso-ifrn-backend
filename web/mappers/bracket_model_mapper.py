from domain.bracket.bracket import Bracket
from domain.match.match import Match
from web.models.response.bracket_config_suggestion_response import (
    BracketConfigSuggestionResponse,
)
from web.models.response.bracket_response import BracketResponse
from web.models.response.match_response import MatchResponse


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
