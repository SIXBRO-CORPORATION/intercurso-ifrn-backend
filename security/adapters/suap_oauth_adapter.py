import httpx
from typing import Optional
from urllib.parse import urlencode

from core.security.oauth_provider_port import SuapOAuthPort
from security.config import settings
from domain.user import User
from domain.exceptions.business_exception import BusinessException


class SUAPOAuthAdapter(SuapOAuthPort):
    def __init__(self):
        self.client_id = settings.suap_client_id
        self.client_secret = settings.suap_client_secret
        self.redirect_uri = settings.suap_redirect_uri
        self.authorization_url = settings.suap_authorization_url
        self.token_url = settings.suap_token_url
        self.user_info_url = settings.suap_user_info_url

    def get_authorization_url(self, state: Optional[str] = None) -> str:
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
        async with httpx.AsyncClient() as client:
            try:
                print(self.redirect_uri)
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

    async def get_user_info(self, access_token: str) -> User:
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
                user = User.from_suap_dict(data)
                return user


            except httpx.HTTPError as e:
                raise BusinessException(f"Erro de conexão com SUAP: {str(e)}")

    async def authenticate_with_code(self, code: str) -> User:
        # Passo 1: Troca código por token
        access_token = await self.exchange_code_for_token(code)

        # Passo 2: Busca dados do usuário
        user_data = await self.get_user_info(access_token)

        return user_data