import httpx
import pytest

from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter

PAYLOAD = {"total_aulas": 640, "total_faltas": 171, "percentual_frequencia": 80}


def _suap(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/"):
        return httpx.Response(200, json=PAYLOAD)
    return httpx.Response(301, headers={"Location": str(request.url) + "/"})


@pytest.mark.asyncio
async def test_attendance_url_has_trailing_slash_and_is_saved():
    async with httpx.AsyncClient(transport=httpx.MockTransport(_suap)) as client:
        result = await SUAPOAuthAdapter()._fetch_attendance(client, "token")
    assert result == PAYLOAD