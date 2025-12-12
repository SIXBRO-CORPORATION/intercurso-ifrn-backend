import httpx
from typing import Optional
from urllib.parse import urlencode

from core.config import settings
from domain.auth_token import SUAPUserData
from domain.exceptions.business_exception import BusinessException


class SUAPOAuthService:
    """
    Serviço para integração OAuth2 com SUAP

    Responsabilidades:
    - Gerar URL de autorização
    - Trocar código por token
    - Buscar dados do usuário no SUAP
    """

    def __init__(self):
        self.client_id = settings.suap_client_id
        self.client_secret = settings.suap_client_secret
        self.redirect_uri = settings.suap_redirect_uri
        self.authorization_url = settings.suap_authorization_url
        self.token_url = settings.suap_token_url
        self.user_info_url = settings.suap_user_info_url

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Gera a URL para redirecionar o usuário ao SUAP

        Args:
            state: String aleatória para prevenir CSRF (recomendado)

        Returns:
            URL completa para redirecionamento
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "email identificacao",  # Escopos do SUAP
        }

        if state:
            params["state"] = state

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
        """
        Troca o código de autorização por um access_token

        Este é o passo 2 do OAuth2: depois que o usuário autoriza no SUAP,
        ele retorna com um 'code'. Você troca esse code por um token.

        Args:
            code: Código retornado pelo SUAP após autorização

        Returns:
            access_token do SUAP

        Raises:
            BusinessException: Se falhar ao trocar o código
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

                if response.status_code != 200:
                    raise BusinessException(
                        f"Erro ao obter token do SUAP: {response.text}"
                    )

                data = response.json()
                return data["access_token"]

            except httpx.HTTPError as e:
                raise BusinessException(f"Erro de conexão com SUAP: {str(e)}")

    async def get_user_info(self, access_token: str) -> SUAPUserData:
        """
        Busca informações do usuário no SUAP usando o access_token

        Args:
            access_token: Token obtido do SUAP

        Returns:
            Dados do usuário parseados

        Raises:
            BusinessException: Se falhar ao buscar dados
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    }
                )

                if response.status_code != 200:
                    raise BusinessException(
                        f"Erro ao buscar dados do usuário no SUAP: {response.text}"
                    )

                data = response.json()

                # Parse dos dados do SUAP
                return SUAPUserData(
                    matricula=str(data.get("matricula", "")),
                    nome_usual=data.get("nome_usual", ""),
                    email=data.get("email", ""),
                    cpf=str(data.get("cpf", "")).replace(".", "").replace("-", ""),
                    tipo_usuario=data.get("tipo_usuario"),
                    campus=data.get("campus"),
                    curso=data.get("vinculo", {}).get("curso") if data.get("vinculo") else None,
                    vinculo=data.get("vinculo")
                )

            except httpx.HTTPError as e:
                raise BusinessException(f"Erro de conexão com SUAP: {str(e)}")

    async def authenticate_with_code(self, code: str) -> SUAPUserData:
        """
        Fluxo completo: troca código por token e busca dados do usuário

        Este é um método conveniente que faz os dois passos:
        1. Troca code por token
        2. Usa o token para buscar dados do usuário

        Args:
            code: Código retornado pelo SUAP

        Returns:
            Dados completos do usuário
        """
        # Passo 1: Troca código por token
        access_token = await self.exchange_code_for_token(code)

        # Passo 2: Busca dados do usuário
        user_data = await self.get_user_info(access_token)

        return user_data