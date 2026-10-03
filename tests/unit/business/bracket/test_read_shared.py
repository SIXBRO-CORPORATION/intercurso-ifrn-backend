from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket._read_shared import load_team_names
from domain.team.team import Team


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
