from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.list_bracket_matches_adapter import ListBracketMatchesAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.team.team import Team


def make_adapter():
    bracket_repository = AsyncMock()
    group_repository = AsyncMock()
    match_repository = AsyncMock()
    team_repository = AsyncMock()
    adapter = ListBracketMatchesAdapter(
        bracket_repository, group_repository, match_repository, team_repository
    )
    return adapter, bracket_repository, group_repository, match_repository, team_repository


class TestListBracketMatchesAdapter:
    @pytest.mark.asyncio
    async def test_returns_matches_with_team_and_group_names(self):
        adapter, bracket_repository, group_repository, match_repository, team_repository = make_adapter()
        bracket_id = uuid4()
        team_id = uuid4()
        group = BracketGroup(id=uuid4(), bracket_id=bracket_id, name="A", display_order=1)
        match = Match(
            bracket_id=bracket_id,
            bracket_group_id=group.id,
            team1_id=team_id,
            team2_id=None,
            status=MatchStatus.SCHEDULED,
        )
        bracket_repository.get.return_value = Bracket(id=bracket_id)
        match_repository.find_by_bracket.return_value = [match]
        group_repository.find_by_bracket.return_value = [group]
        team_repository.find_by_ids.return_value = [Team(id=team_id, name="Time X")]

        context = Context()
        context.put_property("bracket_id", bracket_id)

        result = await adapter.execute(context)

        assert result == [match]
        assert context.get_property("team_names", dict) == {team_id: "Time X"}
        assert context.get_property("group_names", dict) == {group.id: "A"}
        team_repository.find_by_ids.assert_awaited_once_with([team_id])

    @pytest.mark.asyncio
    async def test_blocks_when_bracket_not_found(self):
        adapter, bracket_repository, *_ = make_adapter()
        bracket_repository.get.return_value = None

        context = Context()
        context.put_property("bracket_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)
