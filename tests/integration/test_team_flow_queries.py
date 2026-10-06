"""Queries do fluxo de times executadas no SQL (SQLite em memória)."""

from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from persistence.adapters.team.team_member_repository_adapter import (
    TeamMemberRepositoryAdapter,
)
from persistence.adapters.team.team_repository_adapter import TeamRepositoryAdapter
from persistence.mappers.team.team_member_mapper import TeamMemberMapper
from persistence.mappers.team.team_mapper import TeamMapper
from persistence.mappers.user.user_mapper import UserMapper
from persistence.model.abstract_entity import Base
from persistence.model.team.team_entity import TeamEntity
from persistence.model.team.team_member_entity import TeamMemberEntity
from persistence.model.user.user_entity import UserEntity


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(type_, compiler, **kw):
    return "JSON"


TABLES = [t.__table__ for t in (UserEntity, TeamEntity, TeamMemberEntity)]


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_off(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=OFF")

    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TABLES)
        )
    async with async_sessionmaker(engine, expire_on_commit=False)() as db_session:
        yield db_session
    await engine.dispose()


def make_team(**kwargs) -> TeamEntity:
    defaults = dict(
        id=uuid4(), name="Time", season_id=uuid4(), modality_id=uuid4(),
        owner_id=uuid4(), status="DRAFT", invite_token=str(uuid4()),
        token_active=True, created_at=datetime.now(), modified_at=datetime.now(),
        active=True,
    )
    defaults.update(kwargs)
    return TeamEntity(**defaults)


def make_member(team_id, user_id, donation="PENDING_DONATION", deleted=False) -> TeamMemberEntity:
    return TeamMemberEntity(
        id=uuid4(), team_id=team_id, user_id=user_id, role="MEMBER",
        donation_status=donation, joined_at=datetime.now(),
        created_at=datetime.now(), modified_at=datetime.now(), active=True,
        deleted_at=datetime.now() if deleted else None,
    )


def team_repo(session):
    return TeamRepositoryAdapter(session, TeamMapper())


def member_repo(session):
    return TeamMemberRepositoryAdapter(session, TeamMemberMapper(), UserMapper())


@pytest.mark.integration
class TestTeamFlowQueries:
    async def test_user_teams_filtered_by_season_and_status_in_sql(self, session):
        user = uuid4()
        season_a, season_b = uuid4(), uuid4()
        draft_a = make_team(season_id=season_a, status="DRAFT")
        other_season = make_team(season_id=season_b, status="DRAFT")
        submitted_a = make_team(season_id=season_a, status="SUBMITTED")
        deleted_a = make_team(season_id=season_a, status="DRAFT", deleted_at=datetime.now())
        stranger = make_team(season_id=season_a, status="DRAFT")
        session.add_all([draft_a, other_season, submitted_a, deleted_a, stranger])
        session.add_all([
            make_member(t.id, user) for t in (draft_a, other_season, submitted_a, deleted_a)
        ] + [make_member(stranger.id, uuid4())])
        await session.flush()

        repo = team_repo(session)
        only_draft_a = await repo.find_teams_by_user_id_with_filters(
            user, season_a, TeamStatus.DRAFT
        )
        assert [t.id for t in only_draft_a] == [draft_a.id]

        all_mine = await repo.find_teams_by_user_id_with_filters(user)
        assert {t.id for t in all_mine} == {draft_a.id, other_season.id, submitted_a.id}

    async def test_active_team_user_ids_ignores_deleted_teams_and_memberships(self, session):
        active_user, deleted_team_user, free_user = uuid4(), uuid4(), uuid4()
        active_team = make_team()
        deleted_team = make_team(deleted_at=datetime.now())
        session.add_all([active_team, deleted_team])
        session.add_all([
            make_member(active_team.id, active_user),
            make_member(deleted_team.id, deleted_team_user),
            make_member(active_team.id, free_user, deleted=True),
        ])
        await session.flush()

        result = await team_repo(session).find_user_ids_with_active_teams(
            [active_user, deleted_team_user, free_user]
        )
        assert result == {active_user}
        assert await team_repo(session).find_user_ids_with_active_teams([]) == set()

    async def test_reset_donations_only_touches_non_pending_members_of_team(self, session):
        team = make_team()
        other_team = make_team()
        confirmed = make_member(team.id, uuid4(), donation="DONATION_CONFIRMED")
        pending = make_member(team.id, uuid4())
        other = make_member(other_team.id, uuid4(), donation="DONATION_CONFIRMED")
        session.add_all([team, other_team, confirmed, pending, other])
        await session.flush()

        updated = await member_repo(session).reset_donations_to_pending(team.id)
        await session.refresh(confirmed)
        await session.refresh(other)

        assert updated == 1
        assert confirmed.donation_status == DonationStatus.PENDING_DONATION.value
        assert other.donation_status == DonationStatus.DONATION_CONFIRMED.value
