import httpx
from datetime import date
from typing import Optional
from urllib.parse import urlencode
from core.security.oauth_provider_port import OAuthProviderPort
from security.config import settings
from domain.user.user import User
from domain.exceptions.business_exception import BusinessException


class SUAPOAuthAdapter(OAuthProviderPort):
    def __init__(self):
        self.client_id = settings.suap_client_id
        self.client_secret = settings.suap_client_secret
        self.redirect_uri = settings.suap_redirect_uri
        self.authorization_url = settings.suap_authorization_url
        self.token_url = settings.suap_token_url
        self.user_info_url = settings.suap_user_info_url
        self.identification_url = settings.suap_identification_url

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "email identificacao",
        }

        if state:
            params["state"] = state

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
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
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    raise BusinessException(
                        f"Erro ao obter token do SUAP: {response.text}"
                    )

                data = response.json()
                return data["access_token"]

            except httpx.HTTPError as e:
                raise BusinessException(f"Erro de conexão com SUAP: {str(e)}")

    async def _fetch_json(self, client: httpx.AsyncClient, url: str, access_token: str) -> dict:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise BusinessException(
                f"Erro ao buscar dados do usuário no SUAP ({url}): {response.text}"
            )
        return response.json()

    async def _fetch_attendance(
        self, client: httpx.AsyncClient, access_token: str
    ) -> Optional[dict]:
        # Falha aqui não derruba o login: frequência fica None e a aprovação do time bloqueia.
        url = settings.suap_attendance_url.format(
            ano=settings.attendance_year or date.today().year,
            periodo=settings.attendance_period,
        )
        try:
            response = await client.get(
                url, headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.json() if response.status_code == 200 else None
        except (httpx.HTTPError, ValueError):
            return None

    async def get_user_info(self, access_token: str) -> User:
        async with httpx.AsyncClient() as client:
            try:

                identificacao = await self._fetch_json(
                    client, self.identification_url, access_token
                )

                dados_aluno = None
                if identificacao.get("tipo_usuario") == "Aluno":
                    dados_aluno = await self._fetch_json(
                        client, self.user_info_url, access_token
                    )

                frequencia = None
                if dados_aluno is not None:
                    frequencia = await self._fetch_attendance(client, access_token)

                return User.from_suap_dict(identificacao, dados_aluno, frequencia)

            except httpx.HTTPError as e:
                raise BusinessException(f"Erro de conexão com SUAP: {str(e)}")

    async def authenticate_with_code(self, code: str) -> User:
        access_token = await self.exchange_code_for_token(code)

        user_data = await self.get_user_info(access_token)

        return user_data
