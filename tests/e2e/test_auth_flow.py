import pytest
from httpx import AsyncClient
from web.main import app  # Sua aplicação FastAPI/Flask


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_auth_flow():
    """Testa o fluxo completo de autenticação via API"""

    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Obtém URL de autorização
        response = await client.get("/api/auth/login/suap", follow_redirects=False)

        assert response.status_code in (302, 307)
        assert "location" in response.headers
        assert "suap.ifrn.edu.br" in response.headers["location"]

        # 2. Simula callback com código (em teste real, precisaria do código)
        # response = await client.get("/auth/callback", params={"code": "fake_code"})
        # assert response.status_code == 200
        # assert "access_token" in response.json()