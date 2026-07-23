from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.create_bracket_adapter import CreateBracketAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.modality_format import ModalityFormat
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season
from domain.team.team import Team


def make_adapter():
    bracket_repository = AsyncMock()
    bracket_group_repository = AsyncMock()
    bracket_group_team_repository = AsyncMock()
    match_repository = AsyncMock()
    team_repository = AsyncMock()
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()

    adapter = CreateBracketAdapter(
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
        season_repository,
        season_modality_repository,
    )
    return (
        adapter,
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        team_repository,
        season_repository,
        season_modality_repository,
    )


def make_season(status=SeasonStatus.REGISTRATION_CLOSED):
    return Season(id=uuid4(), name="Intercurso 2026", year=2026, status=status)


def make_approved_teams(n, season_id, modality_id):
    return [
        Team(
            id=uuid4(),
            season_id=season_id,
            modality_id=modality_id,
            status=TeamStatus.APPROVED,
        )
        for _ in range(n)
    ]


def make_context(modality_id, modality_format, configuration=None):
    bracket_shell = Bracket(modality_id=modality_id, format=modality_format)
    context = Context(data=bracket_shell)
    context.put_property("created_by", uuid4())
    context.put_property("configuration", configuration)
    return context


def configure_happy_path(
    bracket_repository,
    season_modality_repository,
    team_repository,
    season_repository,
    season,
    modality_id,
    team_count=8,
    existing_brackets=None,
):
    season_repository.find_active_season.return_value = season
    season_modality_repository.exists_by_season_and_modality.return_value = True
    bracket_repository.exists_active_bracket_for_modality.return_value = False
    bracket_repository.find_by_season.return_value = existing_brackets or []
    approved_teams = make_approved_teams(team_count, season.id, modality_id)
    team_repository.find_approved_teams_by_season_and_modality.return_value = (
        approved_teams
    )
    bracket_repository.save.side_effect = lambda bracket: Bracket(
        id=bracket.id or uuid4(),
        season_id=bracket.season_id,
        modality_id=bracket.modality_id,
        format=bracket.format,
        configuration=bracket.configuration,
        status=bracket.status,
        created_by=bracket.created_by,
    )
    return approved_teams


class TestCreateBracketAdapterSuccess:
    @pytest.mark.asyncio
    async def test_first_bracket_transitions_season_to_in_progress(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()

        modality_id = uuid4()
        season = make_season(SeasonStatus.REGISTRATION_CLOSED)
        configure_happy_path(
            bracket_repository,
            season_modality_repository,
            team_repository,
            season_repository,
            season,
            modality_id,
            team_count=8,
        )

        context = make_context(modality_id, ModalityFormat.KNOCKOUT)
        saved_bracket = await adapter.execute(context)

        assert saved_bracket.status == BracketStatus.ACTIVE
        assert season.status == SeasonStatus.IN_PROGRESS
        season_repository.save.assert_awaited_once()
        assert context.get_property("season_transitioned_to_in_progress", bool) is True
        assert context.get_property("teams_count", int) == 8
        assert context.get_property("matches_created", int) == 8
        assert match_repository.save.await_count == 8

    @pytest.mark.asyncio
    async def test_subsequent_bracket_does_not_transition_season(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()

        modality_id = uuid4()
        season = make_season(SeasonStatus.IN_PROGRESS)
        configure_happy_path(
            bracket_repository,
            season_modality_repository,
            team_repository,
            season_repository,
            season,
            modality_id,
            team_count=4,
            existing_brackets=[Bracket(id=uuid4())],
        )

        context = make_context(modality_id, ModalityFormat.KNOCKOUT)
        await adapter.execute(context)

        season_repository.save.assert_not_awaited()
        assert context.get_property("season_transitioned_to_in_progress", bool) is False

    @pytest.mark.asyncio
    async def test_group_stage_knockout_creates_groups_and_group_teams(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()

        modality_id = uuid4()
        season = make_season(SeasonStatus.REGISTRATION_CLOSED)
        configure_happy_path(
            bracket_repository,
            season_modality_repository,
            team_repository,
            season_repository,
            season,
            modality_id,
            team_count=12,
        )
        bracket_group_repository.save.side_effect = lambda g: type(g)(
            id=uuid4(), bracket_id=g.bracket_id, name=g.name, display_order=g.display_order
        )

        context = make_context(modality_id, ModalityFormat.GROUP_STAGE_KNOCKOUT)
        await adapter.execute(context)

        assert bracket_group_repository.save.await_count == 4
        assert bracket_group_team_repository.save.await_count == 12
        assert context.get_property("groups_created", int) == 4


class TestCreateBracketAdapterValidations:
    @pytest.mark.asyncio
    async def test_blocks_when_no_active_season(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        season_repository.find_active_season.return_value = None

        context = make_context(uuid4(), ModalityFormat.KNOCKOUT)
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_registration_still_open(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        season_repository.find_active_season.return_value = make_season(
            SeasonStatus.REGISTRATION_OPEN
        )

        context = make_context(uuid4(), ModalityFormat.KNOCKOUT)
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_modality_not_in_season(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        season_repository.find_active_season.return_value = make_season()
        season_modality_repository.exists_by_season_and_modality.return_value = False

        context = make_context(uuid4(), ModalityFormat.KNOCKOUT)
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_active_bracket_already_exists(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        season_repository.find_active_season.return_value = make_season()
        season_modality_repository.exists_by_season_and_modality.return_value = True
        bracket_repository.exists_active_bracket_for_modality.return_value = True

        context = make_context(uuid4(), ModalityFormat.KNOCKOUT)
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_less_than_two_approved_teams(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        modality_id = uuid4()
        season = make_season()
        season_repository.find_active_season.return_value = season
        season_modality_repository.exists_by_season_and_modality.return_value = True
        bracket_repository.exists_active_bracket_for_modality.return_value = False
        team_repository.find_approved_teams_by_season_and_modality.return_value = (
            make_approved_teams(1, season.id, modality_id)
        )

        context = make_context(modality_id, ModalityFormat.KNOCKOUT)
        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_triangular_with_wrong_team_count(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            team_repository,
            season_repository,
            season_modality_repository,
        ) = make_adapter()
        modality_id = uuid4()
        season = make_season()
        configure_happy_path(
            bracket_repository,
            season_modality_repository,
            team_repository,
            season_repository,
            season,
            modality_id,
            team_count=4,
        )

        context = make_context(modality_id, ModalityFormat.TRIANGULAR)
        with pytest.raises(BusinessException):
            await adapter.execute(context)
