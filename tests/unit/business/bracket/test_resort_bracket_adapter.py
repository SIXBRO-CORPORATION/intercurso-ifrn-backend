from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.resort_bracket_adapter import ResortBracketAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.enums.modality_format import ModalityFormat
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.team.team import Team


def make_adapter():
    bracket_repository = AsyncMock()
    bracket_group_repository = AsyncMock()
    bracket_group_team_repository = AsyncMock()
    match_repository = AsyncMock()
    team_repository = AsyncMock()

    adapter = ResortBracketAdapter(
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
    )
    return (
        adapter,
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
    )


def make_bracket(modality_format=ModalityFormat.KNOCKOUT, configuration=None):
    return Bracket(
        id=uuid4(),
        season_id=uuid4(),
        modality_id=uuid4(),
        format=modality_format,
        configuration=configuration or {},
        status=BracketStatus.ACTIVE,
        created_by=uuid4(),
    )


class TestResortBracketAdapter:
    @pytest.mark.asyncio
    async def test_resorts_successfully_when_all_matches_scheduled(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
        ) = make_adapter()

        bracket = make_bracket()
        bracket_repository.get.return_value = bracket
        match_repository.find_by_bracket.return_value = [
            Match(id=uuid4(), status=MatchStatus.SCHEDULED)
        ]
        approved_teams = [
            Team(
                id=uuid4(),
                season_id=bracket.season_id,
                modality_id=bracket.modality_id,
                status=TeamStatus.APPROVED,
            )
            for _ in range(4)
        ]
        team_repository.find_approved_teams_by_season_and_modality.return_value = (
            approved_teams
        )
        bracket_repository.save.side_effect = lambda b: b

        context = Context()
        context.put_property("bracket_id", bracket.id)
        context.put_property("requested_by", uuid4())

        result = await adapter.execute(context)

        assert result is bracket
        match_repository.delete_by_bracket.assert_awaited_once_with(bracket.id)
        assert context.get_property("matches_created", int) == 4

    @pytest.mark.asyncio
    async def test_blocks_when_bracket_not_found(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
        ) = make_adapter()
        bracket_repository.get.return_value = None

        context = Context()
        context.put_property("bracket_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_matches_already_started(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
        ) = make_adapter()
        bracket = make_bracket()
        bracket_repository.get.return_value = bracket
        match_repository.find_by_bracket.return_value = [
            Match(id=uuid4(), status=MatchStatus.IN_PROGRESS),
            Match(id=uuid4(), status=MatchStatus.SCHEDULED),
        ]

        context = Context()
        context.put_property("bracket_id", bracket.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        match_repository.delete_by_bracket.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_blocks_when_bracket_status_finished(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
        ) = make_adapter()
        bracket = make_bracket()
        bracket.status = BracketStatus.FINISHED
        bracket_repository.get.return_value = bracket

        context = Context()
        context.put_property("bracket_id", bracket.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)
