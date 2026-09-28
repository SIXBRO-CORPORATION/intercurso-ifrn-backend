import pytest
from fastapi.testclient import TestClient

import web.main as main


class _Session:
    def __init__(self, fail):
        self.fail = fail

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, *_):
        if self.fail:
            raise ConnectionError("db down")


@pytest.mark.parametrize("fail,code", [(False, 200), (True, 503)])
def test_health_reflects_database(monkeypatch, fail, code):
    monkeypatch.setattr(main, "AsyncSessionLocal", lambda: _Session(fail))

    assert TestClient(main.app).get("/health").status_code == code
