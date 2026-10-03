from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.get_bracket_details_adapter import GetBracketDetailsAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.modality.modality import Modality
from domain.team.team import Team


def make_adapter():
    repos = {
        "bracket": AsyncMock(),
        "group": AsyncMock(),
        "group_team": AsyncMock(),
        "match": AsyncMock(),
        "team": AsyncMock(),
        "modality": AsyncMock(),
    }
    adapter = GetBracketDetailsAdapter(
        repos["bracket"],
        repos["group"],
        repos["group_team"],
        repos["match"],
        repos["team"],
        repos["modality"],
    )
    return adapter, repos


class TestGetBracketDetailsAdapter:
    @pytest.mark.asyncio
    async def test_returns_bracket_with_sorted_groups_teams_and_names(self):
        adapter, repos = make_adapter()
        bracket_id = uuid4()
        modality_id = uuid4()
        team_a, team_b = uuid4(), uuid4()
        bracket = Bracket(
            id=bracket_id,
            modality_id=modality_id,
            status=BracketStatus.ACTIVE,
        )
        group_second = BracketGroup(id=uuid4(), bracket_id=bracket_id, name="B", display_order=2)
        group_first = BracketGroup(id=uuid4(), bracket_id=bracket_id, name="A", display_order=1)

        repos["bracket"].get.return_value = bracket
        repos["match"].find_by_bracket.return_value = [
            Match(team1_id=team_a, team2_id=team_b, status=MatchStatus.SCHEDULED)
        ]
        repos["group"].find_by_bracket.return_value = [group_second, group_first]
        repos["group_team"].find_by_group.side_effect = lambda group_id: [
            BracketGroupTeam(bracket_group_id=group_id, team_id=team_a, points=3)
        ]
        repos["team"].get.side_effect = lambda team_id: Team(id=team_id, name=f"Time {team_id}")
        repos["modality"].find_by_ids.return_value = [Modality(id=modality_id, name="Vôlei")]

        context = Context()
        context.put_property("bracket_id", bracket_id)

        result = await adapter.execute(context)

        assert result is bracket
        groups = context.get_property("bracket_groups", list)
        assert [group.name for group, _ in groups] == ["A", "B"]
        assert context.get_property("modality_name", str) == "Vôlei"
        names = context.get_property("team_names", dict)
        assert team_a in names and team_b in names
        assert context.get_property("bracket_stats", dict)["total_matches"] == 1

    @pytest.mark.asyncio
    async def test_blocks_when_bracket_not_found(self):
        adapter, repos = make_adapter()
        repos["bracket"].get.return_value = None

        context = Context()
        context.put_property("bracket_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_without_bracket_id(self):
        adapter, _ = make_adapter()

        with pytest.raises(BusinessException):
            await adapter.execute(Context())
