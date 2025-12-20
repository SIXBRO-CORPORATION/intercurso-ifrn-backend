from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    database_url: str

    # SUAP OAuth2
    suap_client_id: str
    suap_client_secret: str
    suap_redirect_uri: str
    suap_authorization_url: str = "https://suap.ifrn.edu.br/o/authorize/"
    suap_token_url: str = "https://suap.ifrn.edu.br/o/token/"
    suap_user_info_url: str = "https://suap.ifrn.edu.br/api/eu/"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # App
    app_name: str = "Intercurso API"
    debug: bool = False


settings = Settings()
