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


def test_web_callback_never_puts_access_token_in_url_and_sets_cookie():
    state = generate_oauth_state("web")
    client = _client(_login_port())
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, path="/api/auth")

    r = client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert r.status_code == 307
    assert r.headers["location"] == f"{settings.frontend_url}/auth/callback"
    assert "ACCESS-SECRETO" not in r.headers["location"]
    cookie = r.headers.get_list("set-cookie")
    assert any("refresh_token=refresh-plain" in c and "HttpOnly" in c for c in cookie)


def test_invalid_state_redirects_to_login_with_generic_code():
    r = _client(_login_port()).get(
        "/api/auth/callback", params={"code": "c", "state": "forjado"}
    )

    assert r.status_code == 307
    assert r.headers["location"] == f"{settings.frontend_url}/login?erro=state_invalido"


def test_suap_failure_redirects_without_leaking_details():
    port = MagicMock()
    port.execute = AsyncMock(side_effect=BusinessException("Erro SUAP: segredo interno"))
    state = generate_oauth_state("web")
    client = _client(port)
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, path="/api/auth")

    r = client.get("/api/auth/callback", params={"code": "c", "state": state})

    assert r.status_code == 307
    assert r.headers["location"] == f"{settings.frontend_url}/login?erro=login_falhou"
    assert "segredo" not in r.headers["location"]
