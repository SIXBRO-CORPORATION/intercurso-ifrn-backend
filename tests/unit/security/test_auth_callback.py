from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

import web.main as main
from domain.exceptions.business_exception import BusinessException
from security.config import settings
from security.utils.oauth_state import OAUTH_STATE_COOKIE_NAME, generate_oauth_state
from web.dependencies import get_login_with_suap_port


def _client(port):
    main.app.dependency_overrides[get_login_with_suap_port] = lambda: port
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    main.app.dependency_overrides.clear()


def _login_port(refresh="refresh-plain"):
    port = MagicMock()

    async def execute(context):
        context.put_property("refresh_token", refresh)
        return MagicMock(access_token="ACCESS-SECRETO")

    port.execute = execute
    return port


def test_mobile_callback_redirects_to_deep_link():
    state = generate_oauth_state("mobile")
    client = _client(_login_port())
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, path="/api/auth")

    r = client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert r.status_code == 307
    assert r.headers["location"].startswith(
        f"{settings.mobile_deep_link_scheme}://{settings.mobile_deep_link_path}?"
    )


def test_callback_rejects_web_state():
    state = generate_oauth_state("web")
    client = _client(_login_port())
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, path="/api/auth")

    r = client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert r.headers["location"] == f"{settings.frontend_url}/login?erro=state_invalido"


def test_invalid_state_redirects_to_login_with_generic_code():
    r = _client(_login_port()).get(
        "/api/auth/callback", params={"code": "c", "state": "forjado"}
    )

    assert r.status_code == 307
    assert r.headers["location"] == f"{settings.frontend_url}/login?erro=state_invalido"


def test_web_exchange_returns_token_in_body_and_sets_cookie():
    port = _login_port()
    state = generate_oauth_state("web")

    r = _client(port).post("/api/auth/suap/exchange", json={"code": "c", "state": state})

    assert r.status_code == 200
    assert r.json()["data"]["access_token"] == "ACCESS-SECRETO"
    cookie = r.headers.get_list("set-cookie")
    assert any("refresh_token=refresh-plain" in c and "HttpOnly" in c for c in cookie)


def test_web_exchange_rejects_forged_or_mobile_state():
    client = _client(_login_port())

    for state in ("forjado", generate_oauth_state("mobile")):
        r = client.post("/api/auth/suap/exchange", json={"code": "c", "state": state})
        assert r.status_code == 400


def test_web_exchange_failure_does_not_leak_details():
    port = MagicMock()
    port.execute = AsyncMock(side_effect=BusinessException("Erro SUAP: segredo interno"))
    state = generate_oauth_state("web")

    r = _client(port).post("/api/auth/suap/exchange", json={"code": "c", "state": state})

    assert r.status_code == 400
    assert "segredo" not in r.text
