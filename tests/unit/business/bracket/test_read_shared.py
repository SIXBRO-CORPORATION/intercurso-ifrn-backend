from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket._read_shared import build_bracket_stats, load_team_names
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat
from domain.match.match import Match
from domain.team.team import Team


def make_bracket(bracket_format=ModalityFormat.GROUP_STAGE_KNOCKOUT):
    return Bracket(
        id=uuid4(),
        season_id=uuid4(),
        modality_id=uuid4(),
        format=bracket_format,
        configuration={},
        status=BracketStatus.ACTIVE,
        created_by=uuid4(),
    )


def make_match(category, match_type=MatchType.REGULAR, status=MatchStatus.SCHEDULED, next_match_id=None, team1_id=None, team2_id=None):
    return Match(
        id=uuid4(),
        match_category=category,
        match_type=match_type,
        status=status,
        next_match_id=next_match_id,
        team1_id=team1_id,
        team2_id=team2_id,
    )


class TestBuildBracketStatsDrawKnockoutAction:
    def test_offers_draw_knockout_when_groups_finished_and_not_drawn_yet(self):
        bracket = make_bracket()
        matches = [
            make_match(MatchCategory.GROUP, status=MatchStatus.FINISHED),
            make_match(MatchCategory.KNOCKOUT, match_type=MatchType.REGULAR),
        ]

        stats = build_bracket_stats(bracket, matches)

        assert "draw_knockout" in stats["available_actions"]

    def test_does_not_offer_it_while_group_matches_are_pending(self):
        bracket = make_bracket()
        matches = [
            make_match(MatchCategory.GROUP, status=MatchStatus.IN_PROGRESS),
            make_match(MatchCategory.KNOCKOUT, match_type=MatchType.REGULAR),
        ]

        stats = build_bracket_stats(bracket, matches)

        assert "draw_knockout" not in stats["available_actions"]

    def test_does_not_offer_it_once_already_drawn(self):
        bracket = make_bracket()
        matches = [
            make_match(MatchCategory.GROUP, status=MatchStatus.FINISHED),
            make_match(
                MatchCategory.KNOCKOUT,
                match_type=MatchType.REGULAR,
                team1_id=uuid4(),
                team2_id=uuid4(),
            ),
        ]

        stats = build_bracket_stats(bracket, matches)

        assert "draw_knockout" not in stats["available_actions"]

    def test_does_not_offer_it_for_pure_knockout_brackets(self):
        bracket = make_bracket(bracket_format=ModalityFormat.KNOCKOUT)
        matches = [make_match(MatchCategory.KNOCKOUT, match_type=MatchType.REGULAR)]

        stats = build_bracket_stats(bracket, matches)

        assert "draw_knockout" not in stats["available_actions"]


class TestLoadTeamNames:
    @pytest.mark.asyncio
    async def test_loads_all_names_in_one_query_ignoring_none_and_duplicates(self):
        team_a, team_b = uuid4(), uuid4()
        team_repository = AsyncMock()
        team_repository.find_by_ids.return_value = [
            Team(id=team_a, name="A"),
            Team(id=team_b, name="B"),
        ]

        names = await load_team_names(team_repository, [team_a, None, team_b, team_a])

        assert names == {team_a: "A", team_b: "B"}
        team_repository.find_by_ids.assert_awaited_once()
        queried = team_repository.find_by_ids.await_args.args[0]
        assert sorted(queried) == sorted([team_a, team_b])

    @pytest.mark.asyncio
    async def test_skips_unknown_teams(self):
        team_id = uuid4()
        team_repository = AsyncMock()
        team_repository.find_by_ids.return_value = []

        assert await load_team_names(team_repository, [team_id]) == {}

    @pytest.mark.asyncio
    async def test_does_not_query_without_team_ids(self):
        team_repository = AsyncMock()

        assert await load_team_names(team_repository, [None, None]) == {}
        team_repository.find_by_ids.assert_not_awaited()
