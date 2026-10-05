from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.enums.season_status import SeasonStatus
from domain.season.season import Season
from scheduling.jobs import season_scheduler_jobs as jobs


class FakeSession:
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.unit
async def test_open_job_does_not_deactivate_season_in_progress(monkeypatch):
    session = FakeSession()
    repository = AsyncMock()

    running = Season(id=uuid4(), name="Em andamento", active=True, status=SeasonStatus.IN_PROGRESS)
    draft = Season(id=uuid4(), name="Próxima", active=False, status=SeasonStatus.DRAFT)

    repository.find_draft_ready_to_open.return_value = [draft]
    repository.find_active_season.return_value = running

    monkeypatch.setattr(jobs, "AsyncSessionLocal", lambda: session)
    monkeypatch.setattr(jobs, "SeasonRepositoryAdapter", lambda *_: repository)
    monkeypatch.setattr(jobs, "SeasonMapper", lambda: None)

    await jobs.run_open_seasons_job()

    assert running.active is True
    assert draft.status == SeasonStatus.DRAFT
    assert draft.active is False
    repository.save.assert_not_awaited()


@pytest.mark.unit
async def test_open_job_opens_season_when_no_active_season(monkeypatch):
    session = FakeSession()
    repository = AsyncMock()

    draft = Season(id=uuid4(), name="Próxima", active=False, status=SeasonStatus.DRAFT)
    repository.find_draft_ready_to_open.return_value = [draft]
    repository.find_active_season.return_value = None

    monkeypatch.setattr(jobs, "AsyncSessionLocal", lambda: session)
    monkeypatch.setattr(jobs, "SeasonRepositoryAdapter", lambda *_: repository)
    monkeypatch.setattr(jobs, "SeasonMapper", lambda: None)

    await jobs.run_open_seasons_job()

    assert draft.status == SeasonStatus.REGISTRATION_OPEN
    assert draft.active is True
    repository.save.assert_awaited_once_with(draft)
