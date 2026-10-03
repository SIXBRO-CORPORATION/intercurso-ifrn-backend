"""Executa em SQLite (em memória) as consultas de leitura que antes eram feitas
com N+1 ou filtro em memória, garantindo que o SQL gerado devolve o mesmo que
a lógica Python anterior.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from domain.enums.event_type import EventType
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from persistence.adapters.bracket.bracket_group_team_repository_adapter import (
    BracketGroupTeamRepositoryAdapter,
)
from persistence.adapters.match.match_event_repository_adapter import (
    MatchEventRepositoryAdapter,
)
from persistence.adapters.match.match_repository_adapter import MatchRepositoryAdapter
from persistence.adapters.match.match_set_repository_adapter import (
    MatchSetRepositoryAdapter,
)
from persistence.adapters.season.season_repository_adapter import SeasonRepositoryAdapter
from persistence.adapters.team.team_member_repository_adapter import (
    TeamMemberRepositoryAdapter,
)
from persistence.adapters.team.team_repository_adapter import TeamRepositoryAdapter
from persistence.mappers.bracket.bracket_group_team_mapper import BracketGroupTeamMapper
from persistence.mappers.match.match_event_mapper import MatchEventMapper
from persistence.mappers.match.match_mapper import MatchMapper
from persistence.mappers.match.match_set_mapper import MatchSetMapper
from persistence.mappers.season.season_mapper import SeasonMapper
from persistence.mappers.team.team_member_mapper import TeamMemberMapper
from persistence.mappers.team.team_mapper import TeamMapper
from persistence.mappers.user.user_mapper import UserMapper
from persistence.model.abstract_entity import Base
from persistence.model.bracket.bracket_group_team_entity import BracketGroupTeamEntity
from persistence.model.match.match_entity import MatchEntity
from persistence.model.match.match_event_entity import MatchEventEntity
from persistence.model.match.match_set_entity import MatchSetEntity
from persistence.model.season.season_entity import SeasonEntity
from persistence.model.team.team_entity import TeamEntity
from persistence.model.team.team_member_entity import TeamMemberEntity


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(type_, compiler, **kw):
    return "JSON"


TABLES = [
    entity.__table__
    for entity in (
        BracketGroupTeamEntity,
        MatchEntity,
        MatchEventEntity,
        MatchSetEntity,
        SeasonEntity,
        TeamEntity,
        TeamMemberEntity,
    )
]


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TABLES)
        )
    async with async_sessionmaker(engine, expire_on_commit=False)() as db_session:
        yield db_session
    await engine.dispose()


def make_team(**kwargs) -> TeamEntity:
    defaults = dict(
        id=uuid4(),
        name="Time",
        season_id=uuid4(),
        modality_id=uuid4(),
        owner_id=uuid4(),
        status=TeamStatus.DRAFT.value,
        invite_token=str(uuid4()),
    )
    defaults.update(kwargs)
    return TeamEntity(**defaults)


def make_match(bracket_id, **kwargs) -> MatchEntity:
    defaults = dict(
        id=uuid4(),
        bracket_id=bracket_id,
        match_type="REGULAR",
        match_category="KNOCKOUT",
        status="SCHEDULED",
    )
    defaults.update(kwargs)
    return MatchEntity(**defaults)


def make_event(match_id, event_type: EventType, **kwargs) -> MatchEventEntity:
    defaults = dict(
        id=uuid4(),
        match_id=match_id,
        event_type=event_type.value,
        clock_seconds=100,
    )
    defaults.update(kwargs)
    return MatchEventEntity(**defaults)


class TestTeamQueries:
    async def test_find_by_ids_returns_only_requested_non_deleted_teams(self, session):
        repo = TeamRepositoryAdapter(session, TeamMapper())
        kept, other, deleted = make_team(name="A"), make_team(name="B"), make_team(name="C")
        deleted.deleted_at = datetime.now()
        session.add_all([kept, other, deleted])
        await session.flush()

        found = await repo.find_by_ids([kept.id, deleted.id])

        assert [team.id for team in found] == [kept.id]
        assert await repo.find_by_ids([]) == []

    async def test_find_by_status_and_season_id_filters_in_sql(self, session):
        repo = TeamRepositoryAdapter(session, TeamMapper())
        season_id = uuid4()
        match_both = make_team(season_id=season_id, status=TeamStatus.SUBMITTED.value)
        wrong_status = make_team(season_id=season_id, status=TeamStatus.APPROVED.value)
        wrong_season = make_team(status=TeamStatus.SUBMITTED.value)
        session.add_all([match_both, wrong_status, wrong_season])
        await session.flush()

        found = await repo.find_by_status_and_season_id(TeamStatus.SUBMITTED, season_id)

        assert [team.id for team in found] == [match_both.id]

    async def test_count_approved_teams_by_season_and_modality(self, session):
        repo = TeamRepositoryAdapter(session, TeamMapper())
        season_id, modality_id = uuid4(), uuid4()
        approved = [
            make_team(
                season_id=season_id,
                modality_id=modality_id,
                status=TeamStatus.APPROVED.value,
            )
            for _ in range(3)
        ]
        other_modality = make_team(
            season_id=season_id, status=TeamStatus.APPROVED.value
        )
        not_approved = make_team(
            season_id=season_id,
            modality_id=modality_id,
            status=TeamStatus.SUBMITTED.value,
        )
        deleted = make_team(
            season_id=season_id,
            modality_id=modality_id,
            status=TeamStatus.APPROVED.value,
        )
        deleted.deleted_at = datetime.now()
        session.add_all([*approved, other_modality, not_approved, deleted])
        await session.flush()

        assert (
            await repo.count_approved_teams_by_season_and_modality(season_id, modality_id)
            == 3
        )
        assert (
            await repo.count_approved_teams_by_season_and_modality(season_id, uuid4())
            == 0
        )


class TestTeamMemberQueries:
    async def test_batch_counts_match_per_team_counts(self, session):
        repo = TeamMemberRepositoryAdapter(session, TeamMemberMapper(), UserMapper())
        team_a, team_b, team_without_members = uuid4(), uuid4(), uuid4()
        now = datetime.now(timezone.utc)

        def member(team_id, donation_status, deleted=False):
            entity = TeamMemberEntity(
                id=uuid4(),
                team_id=team_id,
                user_id=uuid4(),
                role="MEMBER",
                donation_status=donation_status,
                joined_at=now,
            )
            if deleted:
                entity.deleted_at = datetime.now()
            return entity

        session.add_all(
            [
                member(team_a, "DONATION_CONFIRMED"),
                member(team_a, "PENDING_DONATION"),
                member(team_a, "PENDING_DONATION"),
                member(team_a, "PENDING_DONATION", deleted=True),
                member(team_b, "DONATION_CONFIRMED"),
            ]
        )
        await session.flush()

        team_ids = [team_a, team_b, team_without_members]
        totals = await repo.count_by_teams(team_ids)
        pending = await repo.count_pending_donations_by_teams(team_ids)

        assert totals == {team_a: 3, team_b: 1}
        assert pending == {team_a: 2}
        for team_id in team_ids:
            assert totals.get(team_id, 0) == await repo.count_by_team(team_id)
            assert pending.get(team_id, 0) == await repo.count_pending_donations_by_team(
                team_id
            )
        assert await repo.count_by_teams([]) == {}
        assert await repo.count_pending_donations_by_teams([]) == {}


class TestBracketGroupTeamQueries:
    async def test_find_by_groups_matches_find_by_group_per_group(self, session):
        repo = BracketGroupTeamRepositoryAdapter(session, BracketGroupTeamMapper())
        group_a, group_b, other_group = uuid4(), uuid4(), uuid4()

        def row(group_id, points, goals_difference=0, goals_for=0, deleted=False):
            entity = BracketGroupTeamEntity(
                id=uuid4(),
                bracket_group_id=group_id,
                team_id=uuid4(),
                points=points,
                goals_difference=goals_difference,
                goals_for=goals_for,
            )
            if deleted:
                entity.deleted_at = datetime.now()
            return entity

        session.add_all(
            [
                row(group_a, 3, 1, 2),
                row(group_a, 3, 2, 2),
                row(group_a, 6),
                row(group_a, 9, deleted=True),
                row(group_b, 1),
                row(other_group, 4),
            ]
        )
        await session.flush()

        batched = await repo.find_by_groups([group_a, group_b])

        assert {row.bracket_group_id for row in batched} == {group_a, group_b}
        for group_id in (group_a, group_b):
            expected = [row.id for row in await repo.find_by_group(group_id)]
            assert [row.id for row in batched if row.bracket_group_id == group_id] == expected
        assert await repo.find_by_groups([]) == []


class TestMatchQueries:
    async def test_find_by_brackets_returns_matches_of_all_brackets(self, session):
        repo = MatchRepositoryAdapter(session, MatchMapper())
        bracket_a, bracket_b, other_bracket = uuid4(), uuid4(), uuid4()
        base = datetime.now(timezone.utc)
        later = make_match(bracket_a, scheduled_date=base + timedelta(hours=2))
        earlier = make_match(bracket_b, scheduled_date=base + timedelta(hours=1))
        ignored = make_match(other_bracket)
        deleted = make_match(bracket_a)
        deleted.deleted_at = datetime.now()
        session.add_all([later, earlier, ignored, deleted])
        await session.flush()

        found = await repo.find_by_brackets([bracket_a, bracket_b])

        assert [match.id for match in found] == [earlier.id, later.id]
        assert await repo.find_by_brackets([]) == []


class TestMatchSetQueries:
    async def test_count_and_find_by_number(self, session):
        repo = MatchSetRepositoryAdapter(session, MatchSetMapper())
        match_id, winner = uuid4(), uuid4()

        def match_set(number, deleted=False, match=match_id):
            entity = MatchSetEntity(
                id=uuid4(),
                match_id=match,
                set_number=number,
                team1_points=25,
                team2_points=20,
                winner_team_id=winner,
            )
            if deleted:
                entity.deleted_at = datetime.now()
            return entity

        second = match_set(2)
        session.add_all(
            [match_set(1), second, match_set(3, deleted=True), match_set(1, match=uuid4())]
        )
        await session.flush()

        assert await repo.count_by_match(match_id) == 2
        assert await repo.count_by_match(uuid4()) == 0
        found = await repo.find_by_match_and_number(match_id, 2)
        assert found is not None and found.id == second.id
        assert await repo.find_by_match_and_number(match_id, 3) is None


class TestMatchEventQueries:
    async def test_find_last_by_match_excluding_types(self, session):
        repo = MatchEventRepositoryAdapter(session, MatchEventMapper())
        match_id = uuid4()
        now = datetime.now()
        goal = make_event(match_id, EventType.GOAL, created_at=now - timedelta(minutes=2))
        period_end = make_event(match_id, EventType.PERIOD_END, created_at=now)
        deleted_card = make_event(
            match_id, EventType.CARD_RED, created_at=now - timedelta(minutes=1)
        )
        deleted_card.deleted_at = now
        other_match_goal = make_event(uuid4(), EventType.GOAL, created_at=now)
        session.add_all([goal, period_end, deleted_card, other_match_goal])
        await session.flush()

        found = await repo.find_last_by_match_excluding_types(
            match_id, [EventType.PERIOD_END, EventType.MATCH_STARTED]
        )

        assert found is not None and found.id == goal.id
        assert (
            await repo.find_last_by_match_excluding_types(
                match_id, [EventType.PERIOD_END, EventType.GOAL]
            )
            is None
        )

    async def test_find_last_by_match_and_type(self, session):
        repo = MatchEventRepositoryAdapter(session, MatchEventMapper())
        match_id = uuid4()
        now = datetime.now()
        first_end = make_event(match_id, EventType.SET_END, created_at=now - timedelta(minutes=10))
        last_end = make_event(match_id, EventType.SET_END, created_at=now - timedelta(minutes=1))
        session.add_all([first_end, last_end, make_event(match_id, EventType.POINT, created_at=now)])
        await session.flush()

        found = await repo.find_last_by_match_and_type(match_id, EventType.SET_END)

        assert found is not None and found.id == last_end.id
        assert await repo.find_last_by_match_and_type(uuid4(), EventType.SET_END) is None

    async def test_find_expulsion_prefers_same_clock_then_earliest(self, session):
        repo = MatchEventRepositoryAdapter(session, MatchEventMapper())
        match_id, player_id = uuid4(), uuid4()
        early = make_event(match_id, EventType.EXPULSION, player_id=player_id, clock_seconds=50)
        same_clock = make_event(match_id, EventType.EXPULSION, player_id=player_id, clock_seconds=200)
        other_player = make_event(match_id, EventType.EXPULSION, player_id=uuid4(), clock_seconds=200)
        not_expulsion = make_event(match_id, EventType.CARD_RED, player_id=player_id, clock_seconds=200)
        session.add_all([early, same_clock, other_player, not_expulsion])
        await session.flush()

        preferred = await repo.find_expulsion_by_player(match_id, player_id, 200)
        fallback = await repo.find_expulsion_by_player(match_id, player_id, 999)
        without_clock = await repo.find_expulsion_by_player(match_id, player_id, None)

        assert preferred is not None and preferred.id == same_clock.id
        assert fallback is not None and fallback.id == early.id
        assert without_clock is not None and without_clock.id == early.id
        assert await repo.find_expulsion_by_player(match_id, uuid4(), 200) is None

    async def test_count_by_team_filters_types_and_boundary(self, session):
        repo = MatchEventRepositoryAdapter(session, MatchEventMapper())
        match_id, team1, team2 = uuid4(), uuid4(), uuid4()
        boundary = datetime.now()
        before = boundary - timedelta(minutes=5)
        after = boundary + timedelta(minutes=5)
        session.add_all(
            [
                make_event(match_id, EventType.GOAL, team_id=team1, created_at=before),
                make_event(match_id, EventType.POINT, team_id=team1, created_at=after),
                make_event(match_id, EventType.POINT, team_id=team1, created_at=after),
                make_event(match_id, EventType.GOAL, team_id=team2, created_at=after),
                make_event(match_id, EventType.CARD_YELLOW, team_id=team2, created_at=after),
                make_event(match_id, EventType.PENALTY_GOAL, team_id=team2, created_at=after),
                make_event(uuid4(), EventType.GOAL, team_id=team1, created_at=after),
            ]
        )
        deleted = make_event(match_id, EventType.GOAL, team_id=team2, created_at=after)
        deleted.deleted_at = datetime.now()
        session.add(deleted)
        await session.flush()

        scoring = (EventType.GOAL, EventType.POINT)
        assert await repo.count_by_team(match_id, scoring) == {team1: 3, team2: 1}
        assert await repo.count_by_team(match_id, scoring, created_after=boundary) == {
            team1: 2,
            team2: 1,
        }
        assert await repo.count_by_team(match_id, (EventType.PENALTY_GOAL,)) == {team2: 1}
        assert await repo.count_by_team(uuid4(), scoring) == {}


class TestSeasonSchedulerQueries:
    async def test_find_draft_ready_to_open(self, session):
        repo = SeasonRepositoryAdapter(session, SeasonMapper())
        now = datetime.now(timezone.utc)

        def season(status, start=None, end=None, deleted=False):
            entity = SeasonEntity(
                id=uuid4(),
                name="Intercurso",
                year=2026,
                status=status.value,
                registration_start_date=start,
                registration_end_date=end,
                created_by=uuid4(),
            )
            if deleted:
                entity.deleted_at = datetime.now()
            return entity

        due = season(SeasonStatus.DRAFT, start=now - timedelta(hours=1))
        future = season(SeasonStatus.DRAFT, start=now + timedelta(days=1))
        without_start = season(SeasonStatus.DRAFT)
        wrong_status = season(SeasonStatus.REGISTRATION_OPEN, start=now - timedelta(hours=1))
        deleted = season(SeasonStatus.DRAFT, start=now - timedelta(hours=1), deleted=True)
        session.add_all([due, future, without_start, wrong_status, deleted])
        await session.flush()

        found = await repo.find_draft_ready_to_open(now)

        assert [s.id for s in found] == [due.id]

    async def test_find_open_with_registration_ended(self, session):
        repo = SeasonRepositoryAdapter(session, SeasonMapper())
        now = datetime.now(timezone.utc)

        def season(status, end=None):
            return SeasonEntity(
                id=uuid4(),
                name="Intercurso",
                year=2026,
                status=status.value,
                registration_end_date=end,
                created_by=uuid4(),
            )

        ended = season(SeasonStatus.REGISTRATION_OPEN, end=now - timedelta(minutes=1))
        still_open = season(SeasonStatus.REGISTRATION_OPEN, end=now + timedelta(days=1))
        without_end = season(SeasonStatus.REGISTRATION_OPEN)
        wrong_status = season(SeasonStatus.DRAFT, end=now - timedelta(minutes=1))
        session.add_all([ended, still_open, without_end, wrong_status])
        await session.flush()

        found = await repo.find_open_with_registration_ended(now)

        assert [s.id for s in found] == [ended.id]
