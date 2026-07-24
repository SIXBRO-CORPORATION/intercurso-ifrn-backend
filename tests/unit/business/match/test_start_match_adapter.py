from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.match.start_match_adapter import StartMatchAdapter
from core.context import Context
from domain.bracket import Bracket
from domain.enums.event_type import EventType
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.match import Match
from domain.match.match_event import MatchEvent
from domain.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.team import Team
from domain.team.team_member import TeamMember
from domain.user import User


def make_adapter():
    match_repository = AsyncMock()
    match_event_repository = AsyncMock()
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    bracket_repository = AsyncMock()
    modality_configuration_repository = AsyncMock()
    modality_repository = AsyncMock()

    adapter = StartMatchAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_configuration_repository,
        modality_repository,
    )

    return (
        adapter,
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_configuration_repository,
        modality_repository,
    )


def make_match(status=MatchStatus.SCHEDULED, team1_id=None, team2_id=None):
    return Match(
        id=uuid4(),
        bracket_id=uuid4(),
        team1_id=team1_id or uuid4(),
        team2_id=team2_id or uuid4(),
        match_type=MatchType.REGULAR,
        match_category=MatchCategory.KNOCKOUT,
        status=status,
        team1_score=0,
        team2_score=0,
        clock_seconds=0,
        clock_running=False,
        current_period=None,
    )


def make_team(status=TeamStatus.APPROVED):
    return Team(id=uuid4(), name="Equipe Teste", status=status)


class TestStartMatchAdapter:
    @pytest.mark.asyncio
    async def test_starts_match_successfully(self):
        (
            adapter,
            match_repository,
            match_event_repository,
            team_repository,
            team_member_repository,
            user_repository,
            bracket_repository,
            modality_configuration_repository,
            modality_repository,
        ) = make_adapter()

        team1 = make_team()
        team2 = make_team()
        match = make_match(team1_id=team1.id, team2_id=team2.id)
        monitor_id = uuid4()

        match_repository.get.return_value = match
        match_repository.save.side_effect = lambda m: m
        match_repository.find_in_progress_by_monitor.return_value = None

        team_repository.get.side_effect = lambda team_id: (
            team1 if team_id == team1.id else team2
        )

        member = TeamMember(
            id=uuid4(), team_id=team1.id, user_id=uuid4(), role=TeamMemberRole.CAPTAIN
        )
        team_member_repository.find_members_by_team_id.return_value = [member]
        user_repository.get.return_value = User(
            id=member.user_id, name="Aluno Teste", matricula="20231010001"
        )

        bracket = Bracket(id=match.bracket_id, season_id=uuid4(), modality_id=uuid4())
        bracket_repository.get.return_value = bracket
        modality_repository.get.return_value = Modality(id=bracket.modality_id, name="Futsal")

        modality_configuration_repository.find_by_modality.return_value = (
            ModalityConfiguration(
                id=uuid4(),
                modality_id=bracket.modality_id,
                num_periods=2,
                period_durations_minutes=20,
            )
        )

        match_event_repository.save.side_effect = lambda e: MatchEvent(
            id=uuid4(), **{k: v for k, v in e.__dict__.items() if k != "id"}
        )

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", monitor_id)

        result = await adapter.execute(context)

        assert result.status == MatchStatus.IN_PROGRESS
        assert result.started_at is not None
        assert result.clock_seconds == 0
        assert result.clock_running is True
        assert result.current_period == 1
        assert result.team1_score == 0
        assert result.team2_score == 0
        assert result.monitor_id == monitor_id

        saved_event = match_event_repository.save.call_args[0][0]
        assert saved_event.event_type == EventType.MATCH_STARTED
        assert saved_event.match_id == match.id

        assert context.get_property("team1", Team) == team1
        assert context.get_property("team2", Team) == team2
        assert len(context.get_property("team1_players", list)) == 1

        modality_configuration_repository.find_by_modality.assert_awaited_once_with(
            bracket.modality_id
        )

    @pytest.mark.asyncio
    async def test_blocks_when_not_scheduled(self):
        adapter, match_repository, *_ = make_adapter()
        match = make_match(status=MatchStatus.IN_PROGRESS)
        match_repository.get.return_value = match

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_team_not_approved(self):
        (
            adapter,
            match_repository,
            _match_event_repository,
            team_repository,
            *_rest,
        ) = make_adapter()

        team1 = make_team(status=TeamStatus.APPROVED)
        team2 = make_team(status=TeamStatus.SUBMITTED)
        match = make_match(team1_id=team1.id, team2_id=team2.id)
        match_repository.get.return_value = match
        team_repository.get.side_effect = lambda team_id: (
            team1 if team_id == team1.id else team2
        )

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_teams_not_defined(self):
        adapter, match_repository, *_ = make_adapter()
        match = Match(
            id=uuid4(),
            bracket_id=uuid4(),
            team1_id=None,
            team2_id=uuid4(),
            status=MatchStatus.SCHEDULED,
        )
        match_repository.get.return_value = match

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_monitor_already_managing_another_match(self):
        (
            adapter,
            match_repository,
            _match_event_repository,
            team_repository,
            *_rest,
        ) = make_adapter()

        team1 = make_team()
        team2 = make_team()
        match = make_match(team1_id=team1.id, team2_id=team2.id)
        monitor_id = uuid4()
        other_match = make_match(status=MatchStatus.IN_PROGRESS)

        match_repository.get.return_value = match
        match_repository.find_in_progress_by_monitor.return_value = other_match
        team_repository.get.side_effect = lambda team_id: (
            team1 if team_id == team1.id else team2
        )

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_does_not_block_when_ongoing_match_is_the_same_match(self):
        (
            adapter,
            match_repository,
            match_event_repository,
            team_repository,
            team_member_repository,
            user_repository,
            bracket_repository,
            modality_configuration_repository,
            modality_repository,
        ) = make_adapter()

        team1 = make_team()
        team2 = make_team()
        match = make_match(team1_id=team1.id, team2_id=team2.id)
        monitor_id = uuid4()

        match_repository.get.return_value = match
        match_repository.save.side_effect = lambda m: m
        # Situação hipotética: o próprio match_id já retornado como "em andamento"
        # pelo monitor não deve bloquear o início.
        match_repository.find_in_progress_by_monitor.return_value = match
        team_repository.get.side_effect = lambda team_id: (
            team1 if team_id == team1.id else team2
        )
        team_member_repository.find_members_by_team_id.return_value = []
        bracket_repository.get.return_value = None
        match_event_repository.save.side_effect = lambda e: e

        context = Context()
        context.put_property("match_id", match.id)
        context.put_property("monitor_id", monitor_id)

        result = await adapter.execute(context)

        assert result.status == MatchStatus.IN_PROGRESS
