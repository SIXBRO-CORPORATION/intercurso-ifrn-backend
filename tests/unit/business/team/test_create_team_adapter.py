from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.create_team_adapter import CreateTeamAdapter
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season
from domain.team import Team
from domain.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()
    modality_repository = AsyncMock()

    adapter = CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
    )
    return (
        adapter,
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
    )


def make_open_season(season_id=None):
    return Season(
        id=season_id or uuid4(),
        name="Intercurso 2026",
        status=SeasonStatus.REGISTRATION_OPEN,
        registration_start_date=datetime.now() - timedelta(days=1),
        registration_end_date=datetime.now() + timedelta(days=5),
    )


def make_context(name="Time A", modality_id=None, creator_user_id=None):
    team = Team(name=name, modality_id=modality_id or uuid4())
    context = Context(data=team)
    context.put_property(
        "creator_user_id", creator_user_id if creator_user_id is not None else uuid4()
    )
    return context, team


@pytest.mark.unit
class TestCreateTeamAdapter:
    async def test_creates_team_with_owner_member(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()

        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.find_teams_by_user_id.return_value = []

        saved_team = Team(
            id=uuid4(),
            name=team.name,
            modality_id=team.modality_id,
            season_id=active_season.id,
            owner_id=creator_user_id,
        )
        team_repository.save.return_value = saved_team
        user_repository.get.return_value = User(id=creator_user_id, atleta=False)

        result = await adapter.execute(context)

        assert result.id == saved_team.id
        team_repository.save.assert_awaited_once()
        team_member_repository.save.assert_awaited_once()
        user_repository.save.assert_awaited_once()

        owner_member = context.get_property("owner_member", object)
        assert owner_member is not None

    async def test_blocks_when_no_active_season(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_season_not_registration_open(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.status = SeasonStatus.REGISTRATION_CLOSED
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_period_not_started(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.registration_start_date = datetime.now() + timedelta(days=1)
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_period_ended(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.registration_end_date = datetime.now() - timedelta(days=1)
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_modality_does_not_exist(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = make_open_season()
        modality_repository.exists_by_id.return_value = False

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_modality_not_in_active_season(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = make_open_season()
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = False

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_user_already_has_team_in_modality(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True

        existing_team = Team(
            id=uuid4(),
            season_id=active_season.id,
            modality_id=team.modality_id,
        )
        team_repository.find_teams_by_user_id.return_value = [existing_team]

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_data_is_missing(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        context = Context()
        context.put_property("creator_user_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_creator_user_id_is_missing(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        team = Team(name="Time A", modality_id=uuid4())
        context = Context(data=team)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_marks_creator_as_atleta_when_not_already(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.find_teams_by_user_id.return_value = []
        team_repository.save.return_value = Team(id=uuid4(), name=team.name)

        creator_user = User(id=creator_user_id, atleta=False)
        user_repository.get.return_value = creator_user

        await adapter.execute(context)

        assert creator_user.atleta is True
        user_repository.save.assert_awaited_once_with(creator_user)

    async def test_does_not_resave_user_already_atleta(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.find_teams_by_user_id.return_value = []
        team_repository.save.return_value = Team(id=uuid4(), name=team.name)

        user_repository.get.return_value = User(id=creator_user_id, atleta=True)

        await adapter.execute(context)

        user_repository.save.assert_not_awaited()
