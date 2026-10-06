from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.season.season_modality import SeasonModality
from domain.user.user import User
from persistence.adapters.bracket.bracket_group_repository_adapter import (
    BracketGroupRepositoryAdapter,
)
from persistence.adapters.bracket.bracket_group_team_repository_adapter import (
    BracketGroupTeamRepositoryAdapter,
)
from persistence.adapters.season.season_modality_repository_adapter import (
    SeasonModalityRepositoryAdapter,
)
from persistence.adapters.user.user_repository_adapter import UserRepositoryAdapter
from persistence.mappers.bracket.bracket_group_mapper import BracketGroupMapper
from persistence.mappers.bracket.bracket_group_team_mapper import BracketGroupTeamMapper
from persistence.mappers.season.season_modality_mapper import SeasonModalityMapper
from persistence.mappers.user.user_mapper import UserMapper
from persistence.model.abstract_entity import Base
from persistence.model.bracket.bracket_group_entity import BracketGroupEntity
from persistence.model.bracket.bracket_group_team_entity import BracketGroupTeamEntity
from persistence.model.season.season_modality_entity import SeasonModalityEntity
from persistence.model.user.user_entity import UserEntity


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


TABLES = [
    e.__table__
    for e in (BracketGroupEntity, BracketGroupTeamEntity, SeasonModalityEntity, UserEntity)
]


@pytest_asyncio.fixture
async def session_and_statements():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TABLES))
    statements: list[str] = []
    event.listen(
        engine.sync_engine,
        "before_cursor_execute",
        lambda conn, cur, stmt, *a: statements.append(stmt),
    )
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session, statements
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insert_all_persists_batch_without_per_row_selects(session_and_statements):
    session, statements = session_and_statements
    groups_repo = BracketGroupRepositoryAdapter(session, BracketGroupMapper())
    teams_repo = BracketGroupTeamRepositoryAdapter(session, BracketGroupTeamMapper())
    modalities_repo = SeasonModalityRepositoryAdapter(session, SeasonModalityMapper())
    bracket_id, season_id = uuid4(), uuid4()

    statements.clear()
    groups = await groups_repo.insert_all(
        [BracketGroup(bracket_id=bracket_id, name=n, display_order=i) for i, n in enumerate("ABC")]
    )
    await teams_repo.insert_all(
        [
            BracketGroupTeam(bracket_group_id=g.id, team_id=uuid4(), points=0, wins=0,
                             draws=0, losses=0, goals_for=0, goals_against=0, goals_difference=0)
            for g in groups
            for _ in range(4)
        ]
    )
    saved = await modalities_repo.insert_all(
        [SeasonModality(season_id=season_id, modality_id=uuid4()) for _ in range(3)]
    )

    during_inserts = list(statements)

    assert not [s for s in during_inserts if s.lstrip().upper().startswith("SELECT")]
    assert [g.name for g in groups] == ["A", "B", "C"]
    assert all(g.id and g.created_at for g in groups)
    assert all(s.id and s.created_at for s in saved)
    assert len(await groups_repo.find_by_bracket(bracket_id)) == 3
    assert len(await teams_repo.find_by_groups([g.id for g in groups])) == 12


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clear_atleta_updates_only_given_athletes_in_one_statement(session_and_statements):
    session, statements = session_and_statements
    repo = UserRepositoryAdapter(session, UserMapper())
    def mk(atleta):
        return User(
            id=uuid4(),
            name="x",
            cpf=str(uuid4().int)[:11],
            matricula=str(uuid4().int)[:14],
            atleta=atleta,
        )
    freed, kept, not_athlete = mk(True), mk(True), mk(False)
    for u in (freed, kept, not_athlete):
        await repo.save(u)

    statements.clear()
    assert await repo.clear_atleta([freed.id, not_athlete.id]) == 1
    assert len([s for s in statements if s.lstrip().upper().startswith("UPDATE")]) == 1

    flags = {e.id: e.atleta for e in (await session.execute(select(UserEntity))).scalars()}
    assert flags == {freed.id: False, kept.id: True, not_athlete.id: False}
    assert await repo.clear_atleta([]) == 0
