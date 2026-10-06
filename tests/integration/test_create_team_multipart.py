"""POST /api/team/ em multipart: texto + foto opcional no mesmo request."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from domain.team.team import Team
from domain.user.user import User
from web.dependencies import get_create_team_port, get_team_model_mapper
from web.dependencies.security_dependencies import require_authenticated_user
from web.main import app

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture
def client_and_port():
    user = User(id=uuid4(), name="Aluno")
    port = AsyncMock()
    port.execute.side_effect = lambda ctx: Team(
        id=uuid4(), name="Time A", modality_id=ctx.get_data(Team).modality_id,
        owner_id=user.id, invite_token="tok",
    )
    mapper = AsyncMock()
    mapper.to_register_response = lambda *a, **k: {
        "team_id": str(uuid4()), "name": "Time A", "modality_id": str(uuid4()),
        "status": "DRAFT", "photo": None, "invite_token": "tok",
        "owner_id": str(user.id), "message": "ok",
    }
    app.dependency_overrides[require_authenticated_user] = lambda: user
    app.dependency_overrides[get_create_team_port] = lambda: port
    app.dependency_overrides[get_team_model_mapper] = lambda: mapper
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://t"), port
    app.dependency_overrides.clear()


async def test_accepts_fields_and_photo_in_one_request(client_and_port):
    client, port = client_and_port
    r = await client.post(
        "/api/team/",
        data={"name": "  Time A ", "modality_id": str(uuid4())},
        files={"photo": ("logo.png", PNG, "image/png")},
    )
    assert r.status_code == 201, r.text
    ctx = port.execute.await_args.args[0]
    assert ctx.get("photo_bytes") == PNG
    assert ctx.get_data(Team).name == "Time A"


async def test_photo_is_optional(client_and_port):
    client, port = client_and_port
    r = await client.post(
        "/api/team/", data={"name": "Time A", "modality_id": str(uuid4())}
    )
    assert r.status_code == 201, r.text
    assert port.execute.await_args.args[0].get("photo_bytes") is None


async def test_rejects_blank_or_short_name_with_422(client_and_port):
    client, port = client_and_port
    for name in ("ab", "    "):
        r = await client.post(
            "/api/team/", data={"name": name, "modality_id": str(uuid4())}
        )
        assert r.status_code == 422
    port.execute.assert_not_awaited()
