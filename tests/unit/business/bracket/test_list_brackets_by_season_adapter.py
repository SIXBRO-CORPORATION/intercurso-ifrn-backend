from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.list_brackets_by_season_adapter import ListBracketsBySeasonAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.modality.modality import Modality


def make_adapter():
    bracket_repository = AsyncMock()
    match_repository = AsyncMock()
    modality_repository = AsyncMock()
    adapter = ListBracketsBySeasonAdapter(
        bracket_repository, match_repository, modality_repository
    )
    return adapter, bracket_repository, match_repository, modality_repository


class TestListBracketsBySeasonAdapter:
    @pytest.mark.asyncio
    async def test_returns_brackets_with_stats_and_modality_names(self):
        adapter, bracket_repository, match_repository, modality_repository = make_adapter()
        season_id = uuid4()
        modality_id = uuid4()
        bracket = Bracket(
            id=uuid4(),
            season_id=season_id,
            modality_id=modality_id,
            status=BracketStatus.ACTIVE,
        )
        bracket_repository.find_by_season.return_value = [bracket]
        match_repository.find_by_brackets.return_value = [
            Match(bracket_id=bracket.id, status=MatchStatus.IN_PROGRESS),
            Match(bracket_id=bracket.id, status=MatchStatus.FINISHED),
            Match(bracket_id=bracket.id, status=MatchStatus.SCHEDULED),
        ]
        modality_repository.find_by_ids.return_value = [
            Modality(id=modality_id, name="Futsal")
        ]

        context = Context()
        context.put_property("season_id", season_id)

        result = await adapter.execute(context)

        assert result == [bracket]
        stats = context.get_property("bracket_stats", dict)
        assert stats[bracket.id]["total_matches"] == 3
        assert stats[bracket.id]["started_matches"] == 2
        assert stats[bracket.id]["finished_matches"] == 1
        assert stats[bracket.id]["available_actions"] == []
        assert context.get_property("modality_names", dict) == {modality_id: "Futsal"}

    @pytest.mark.asyncio
    async def test_loads_matches_of_all_brackets_in_one_query(self):
        adapter, bracket_repository, match_repository, modality_repository = make_adapter()
        season_id = uuid4()
        bracket_a = Bracket(
            id=uuid4(), season_id=season_id, modality_id=uuid4(), status=BracketStatus.ACTIVE
        )
        bracket_b = Bracket(
            id=uuid4(), season_id=season_id, modality_id=uuid4(), status=BracketStatus.ACTIVE
        )
        bracket_c = Bracket(
            id=uuid4(), season_id=season_id, modality_id=uuid4(), status=BracketStatus.DRAFT
        )
        bracket_repository.find_by_season.return_value = [bracket_a, bracket_b, bracket_c]
        match_repository.find_by_brackets.return_value = [
            Match(bracket_id=bracket_a.id, status=MatchStatus.FINISHED),
            Match(bracket_id=bracket_b.id, status=MatchStatus.SCHEDULED),
            Match(bracket_id=bracket_a.id, status=MatchStatus.SCHEDULED),
        ]
        modality_repository.find_by_ids.return_value = []

        context = Context()
        context.put_property("season_id", season_id)

        await adapter.execute(context)

        match_repository.find_by_brackets.assert_awaited_once_with(
            [bracket_a.id, bracket_b.id, bracket_c.id]
        )
        stats = context.get_property("bracket_stats", dict)
        assert stats[bracket_a.id]["total_matches"] == 2
        assert stats[bracket_a.id]["finished_matches"] == 1
        assert stats[bracket_b.id]["total_matches"] == 1
        assert stats[bracket_c.id]["total_matches"] == 0

    @pytest.mark.asyncio
    async def test_offers_resort_when_no_match_started(self):
        adapter, bracket_repository, match_repository, modality_repository = make_adapter()
        season_id = uuid4()
        bracket = Bracket(
            id=uuid4(),
            season_id=season_id,
            modality_id=uuid4(),
            status=BracketStatus.ACTIVE,
        )
        bracket_repository.find_by_season.return_value = [bracket]
        match_repository.find_by_brackets.return_value = [
            Match(bracket_id=bracket.id, status=MatchStatus.SCHEDULED)
        ]
        modality_repository.find_by_ids.return_value = []

        context = Context()
        context.put_property("season_id", season_id)

        await adapter.execute(context)

        stats = context.get_property("bracket_stats", dict)
        assert stats[bracket.id]["available_actions"] == ["resort"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_without_querying_matches(self):
        adapter, bracket_repository, match_repository, modality_repository = make_adapter()
        bracket_repository.find_by_season.return_value = []

        context = Context()
        context.put_property("season_id", uuid4())

        result = await adapter.execute(context)

        assert result == []
        match_repository.find_by_brackets.assert_not_awaited()
        modality_repository.find_by_ids.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_blocks_without_season_id(self):
        adapter, *_ = make_adapter()

        with pytest.raises(BusinessException):
            await adapter.execute(Context())
