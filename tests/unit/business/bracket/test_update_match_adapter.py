from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.update_match_adapter import UpdateMatchAdapter
from core.context import Context
from domain.bracket import Bracket
from domain.enums.match_status import MatchStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.match import Match
from domain.team import Team


def make_adapter():
    match_repository = AsyncMock()
    bracket_repository = AsyncMock()
    team_repository = AsyncMock()
    adapter = UpdateMatchAdapter(match_repository, bracket_repository, team_repository)
    return adapter, match_repository, bracket_repository, team_repository


class TestUpdateMatchAdapter:
    @pytest.mark.asyncio
    async def test_updates_scheduled_date_only(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()
        match = Match(id=uuid4(), bracket_id=uuid4(), status=MatchStatus.SCHEDULED)
        match_repository.get.return_value = match
        match_repository.save.side_effect = lambda m: m

        new_date = datetime.now() + timedelta(days=1)
        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("scheduled_date", new_date)
        context.put_property("team1_id", None)
        context.put_property("team2_id", None)

        result = await adapter.execute(context)

        assert result.scheduled_date == new_date
        bracket_repository.get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_swaps_team_when_approved_and_same_modality(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()
        bracket = Bracket(id=uuid4(), season_id=uuid4(), modality_id=uuid4())
        match = Match(id=uuid4(), bracket_id=bracket.id, status=MatchStatus.SCHEDULED)
        match_repository.get.return_value = match
        match_repository.save.side_effect = lambda m: m
        bracket_repository.get.return_value = bracket

        new_team = Team(
            id=uuid4(),
            season_id=bracket.season_id,
            modality_id=bracket.modality_id,
            status=TeamStatus.APPROVED,
        )
        team_repository.get.return_value = new_team

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("team2_id", new_team.id)

        result = await adapter.execute(context)

        assert result.team2_id == new_team.id

    @pytest.mark.asyncio
    async def test_blocks_team_from_different_modality(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()
        bracket = Bracket(id=uuid4(), season_id=uuid4(), modality_id=uuid4())
        match = Match(id=uuid4(), bracket_id=bracket.id, status=MatchStatus.SCHEDULED)
        match_repository.get.return_value = match
        bracket_repository.get.return_value = bracket

        other_team = Team(
            id=uuid4(),
            season_id=bracket.season_id,
            modality_id=uuid4(),  # modalidade diferente
            status=TeamStatus.APPROVED,
        )
        team_repository.get.return_value = other_team

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("team1_id", other_team.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_team_not_approved(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()
        bracket = Bracket(id=uuid4(), season_id=uuid4(), modality_id=uuid4())
        match = Match(id=uuid4(), bracket_id=bracket.id, status=MatchStatus.SCHEDULED)
        match_repository.get.return_value = match
        bracket_repository.get.return_value = bracket

        pending_team = Team(
            id=uuid4(),
            season_id=bracket.season_id,
            modality_id=bracket.modality_id,
            status=TeamStatus.SUBMITTED,
        )
        team_repository.get.return_value = pending_team

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("team1_id", pending_team.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_match_not_scheduled(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()
        match = Match(id=uuid4(), bracket_id=uuid4(), status=MatchStatus.IN_PROGRESS)
        match_repository.get.return_value = match

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("scheduled_date", datetime.now())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_no_fields_provided(self):
        adapter, match_repository, bracket_repository, team_repository = make_adapter()

        context = Context()
        context.put_property("match_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)
