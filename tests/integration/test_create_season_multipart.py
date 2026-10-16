"""POST /api/season/ em multipart: texto + regulamento opcional no mesmo request."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from domain.season.season import Season
from domain.user.user import User
from web.dependencies import get_create_season_port, get_season_model_mapper
from web.dependencies.security_dependencies import require_monitor
from web.main import app

PDF = b"%PDF-1.4" + b"0" * 32


@pytest.fixture
def client_and_port():
    user = User(id=uuid4(), name="Monitor")
    port = AsyncMock()
    port.execute.side_effect = lambda ctx: Season(
        id=uuid4(), name=ctx.get_data(Season).name, year=ctx.get_data(Season).year,
    )
    mapper = AsyncMock()
    mapper.to_create_response = lambda *a, **k: {
        "season_id": str(uuid4()), "name": "Intercurso 2026", "year": 2026,
        "status": "DRAFT", "active": False, "registration_start_date": None,
        "registration_end_date": None, "modality_ids": [], "rules_document": None,
        "message": "ok",
    }
    app.dependency_overrides[require_monitor] = lambda: user
    app.dependency_overrides[get_create_season_port] = lambda: port
    app.dependency_overrides[get_season_model_mapper] = lambda: mapper
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://t"), port
    app.dependency_overrides.clear()


def _form_data(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "name": "Intercurso 2026",
        "year": "2026",
        "modality_ids": [str(uuid4())],
        "registration_start_date": (now + timedelta(days=1)).isoformat(),
        "registration_end_date": (now + timedelta(days=10)).isoformat(),
    }
    data.update(overrides)
    return data


async def test_accepts_fields_and_rules_document_in_one_request(client_and_port):
    client, port = client_and_port
    r = await client.post(
        "/api/season/",
        data=_form_data(),
        files={"rules_document": ("regulamento.pdf", PDF, "application/pdf")},
    )
    assert r.status_code == 201, r.text
    ctx = port.execute.await_args.args[0]
    assert ctx.get("rules_document_bytes") == PDF
    assert ctx.get_data(Season).name == "Intercurso 2026"


async def test_rules_document_is_optional(client_and_port):
    client, port = client_and_port
    r = await client.post("/api/season/", data=_form_data())
    assert r.status_code == 201, r.text
    assert port.execute.await_args.args[0].get("rules_document_bytes") is None


async def test_rejects_blank_name_with_422(client_and_port):
    client, port = client_and_port
    r = await client.post("/api/season/", data=_form_data(name="   "))
    assert r.status_code == 422
    port.execute.assert_not_awaited()
