
import pytest
from security.adapters.suap_oauth_adapter import SUAPOAuthAdapter


@pytest.mark.integration
@pytest.mark.asyncio
async def test_suap_oauth_real_flow():
    """
    Teste manual - requer código de autorização real do SUAP
    Execute com: pytest -m integration -s
    """
    adapter = SUAPOAuthAdapter()

    # 1. Gera URL de autorização
    auth_url = adapter.get_authorization_url(state="test_state")
    print(f"\n🔗 Acesse: {auth_url}")
    print("⏳ Aguardando autorização...")

    # 2. Aguarda código (em teste real, você copiaria da URL de callback)
    # authorization_code = input("Cole o código de autorização: ")

    # 3. Troca código por token
    # access_token = await adapter.exchange_code_for_token(authorization_code)
    # assert access_token is not None

    # 4. Busca dados do usuário
    # user_data = await adapter.get_user_info(access_token)
    # assert user_data.matricula is not None
    # assert user_data.email is not None