"""Listagens públicas da aba Jogos (ADR 0004 / UC016): modalidades e partidas.

Query em SQLite em memória (persistence) + rota HTTP sem autenticação (ASGI).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from business.match.list_public_matches_adapter import ListPublicMatchesAdapter
from domain.enums.match_status import MatchStatus
from persistence.adapters.bracket.bracket_group_repository_adapter import (
    BracketGroupRepositoryAdapter,
)
from persistence.adapters.bracket.bracket_repository_adapter import (
    BracketRepositoryAdapter,
)
from persistence.adapters.match.match_repository_adapter import MatchRepositoryAdapter
from persistence.adapters.modality.modality_repository_adapter import (
    ModalityRepositoryAdapter,
)
from persistence.adapters.team.team_repository_adapter import TeamRepositoryAdapter
from persistence.mappers.bracket.bracket_group_mapper import BracketGroupMapper
from persistence.mappers.bracket.bracket_mapper import BracketMapper
from persistence.mappers.match.match_mapper import MatchMapper
from persistence.mappers.modality.modality_mapper import ModalityMapper
from persistence.mappers.team.team_mapper import TeamMapper
from persistence.model.abstract_entity import Base
from persistence.model.bracket.bracket_entity import BracketEntity
from persistence.model.bracket.bracket_group_entity import BracketGroupEntity
from persistence.model.match.match_entity import MatchEntity
from persistence.model.modality.modality_entity import ModalityEntity
from persistence.model.season.season_modality_entity import SeasonModalityEntity
from persistence.model.team.team_entity import TeamEntity
from web.dependencies.business.match_dependencies import get_list_public_matches_port
from web.main import app


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(type_, compiler, **kw):
    return "JSON"


TABLES = [
    e.__table__
    for e in (
        BracketEntity,
        BracketGroupEntity,
        MatchEntity,
        ModalityEntity,
        SeasonModalityEntity,
        TeamEntity,
    )
]


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TABLES))
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    await engine.dispose()


def bracket(season_id, modality_id, **kw):
    return BracketEntity(
        id=uuid4(), season_id=season_id, modality_id=modality_id,
        format="KNOCKOUT", status="ACTIVE", created_by=uuid4(), **kw,
    )


def match(bracket_id, **kw):
    d = dict(id=uuid4(), bracket_id=bracket_id, match_type="REGULAR",
             match_category="KNOCKOUT", status="SCHEDULED")
    d.update(kw)
    return MatchEntity(**d)


class TestSearchBySeason:
    async def test_filters_orders_and_paginates_in_sql(self, session):
        repo = MatchRepositoryAdapter(session, MatchMapper())
        season, other_season, futsal, volei = uuid4(), uuid4(), uuid4(), uuid4()
        b_futsal, b_volei, b_other = (
            bracket(season, futsal), bracket(season, volei), bracket(other_season, futsal)
        )
        now = datetime.now(timezone.utc)
        m_late = match(b_futsal.id, scheduled_date=now + timedelta(hours=3))
        m_early = match(b_futsal.id, scheduled_date=now + timedelta(hours=1), status="FINISHED")
        m_undated = match(b_futsal.id)
        m_volei = match(b_volei.id, scheduled_date=now + timedelta(hours=2))
        bye = match(b_futsal.id, is_bye=True)
        deleted = match(b_futsal.id, deleted_at=datetime.now())
        other = match(b_other.id)
        session.add_all([b_futsal, b_volei, b_other, m_late, m_early, m_undated, m_volei, bye, deleted, other])
        await session.flush()

        everything, total = await repo.search_by_season(season, None, None, None, None, 0, 10)
        assert total == 4
        assert [m.id for m in everything] == [m_early.id, m_volei.id, m_late.id, m_undated.id]  # sem data por último

        only_futsal, total = await repo.search_by_season(season, futsal, None, None, None, 0, 10)
        assert total == 3 and m_volei.id not in {m.id for m in only_futsal}

        finished, total = await repo.search_by_season(season, None, MatchStatus.FINISHED, None, None, 0, 10)
        assert [m.id for m in finished] == [m_early.id] and total == 1

        window, total = await repo.search_by_season(
            season, None, None, now + timedelta(hours=1, minutes=30), now + timedelta(hours=2, minutes=30), 0, 10
        )
        assert [m.id for m in window] == [m_volei.id] and total == 1

        page2, total = await repo.search_by_season(season, None, None, None, None, 2, 2)
        assert [m.id for m in page2] == [m_late.id, m_undated.id] and total == 4  # total ignora a paginação


class TestModalitiesBySeason:
    async def test_returns_only_active_modalities_of_the_season_ordered_by_name(self, session):
        repo = ModalityRepositoryAdapter(session, ModalityMapper())
        season, other = uuid4(), uuid4()
        volei = ModalityEntity(id=uuid4(), name="Vôlei", min_members=6, max_members=12)
        futsal = ModalityEntity(id=uuid4(), name="Futsal", min_members=5, max_members=10)
        inactive = ModalityEntity(id=uuid4(), name="Xadrez", min_members=1, max_members=1, active=False)
        elsewhere = ModalityEntity(id=uuid4(), name="Basquete", min_members=5, max_members=10)
        session.add_all([volei, futsal, inactive, elsewhere])
        session.add_all([
            SeasonModalityEntity(id=uuid4(), season_id=season, modality_id=m.id)
            for m in (volei, futsal, inactive)
        ] + [SeasonModalityEntity(id=uuid4(), season_id=other, modality_id=elsewhere.id)])
        await session.flush()

        found = await repo.find_active_by_season(season)

        assert [m.name for m in found] == ["Futsal", "Vôlei"]


class TestPublicMatchListEndToEnd:
    async def test_visitor_lists_matches_without_token_and_without_matricula(self, session):
        season, modality = uuid4(), ModalityEntity(id=uuid4(), name="Futsal", min_members=5, max_members=10)
        br = bracket(season, modality.id)
        group = BracketGroupEntity(id=uuid4(), bracket_id=br.id, name="A", display_order=1)
        t1 = TeamEntity(id=uuid4(), name="Time A", season_id=season, modality_id=modality.id,
                        owner_id=uuid4(), invite_token="x", photo="logo.png")
        live = match(br.id, status="IN_PROGRESS", bracket_group_id=group.id, team1_id=t1.id,
                     team1_score=2, team2_score=0, clock_seconds=90, clock_running=False)
        tbd = match(br.id, scheduled_date=datetime.now(timezone.utc))
        session.add_all([modality, br, group, t1, live, tbd])
        await session.flush()

        app.dependency_overrides[get_list_public_matches_port] = lambda: ListPublicMatchesAdapter(
            MatchRepositoryAdapter(session, MatchMapper()),
            BracketRepositoryAdapter(session, BracketMapper()),
            BracketGroupRepositoryAdapter(session, BracketGroupMapper()),
            TeamRepositoryAdapter(session, TeamMapper()),
            ModalityRepositoryAdapter(session, ModalityMapper()),
        )
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
                ok = await client.get("/api/match/", params={"season_id": str(season), "size": 10})
                too_big = await client.get("/api/match/", params={"season_id": str(season), "size": 101})
                no_season = await client.get("/api/match/")
        finally:
            app.dependency_overrides.pop(get_list_public_matches_port, None)

        assert ok.status_code == 200 and too_big.status_code == 422 and no_season.status_code == 422
        data = ok.json()["data"]
        assert data["total"] == 2 and data["page"] == 1 and data["size"] == 10
        by_status = {i["status"]: i for i in data["items"]}
        item = by_status["IN_PROGRESS"]
        assert item["modality_name"] == "Futsal" and item["group_name"] == "A"
        assert item["team1"]["name"] == "Time A" and item["team1"]["photo"] == "logo.png"
        assert item["team1"]["score"] == 2 and item["team2"] is None  # A definir
        assert "matricula" not in ok.text
