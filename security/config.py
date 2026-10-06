from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    database_url_sync: str

    # SUAP OAuth2
    suap_client_id: str
    suap_client_secret: str
    suap_redirect_uri: str
    suap_authorization_url: str = "https://suap.ifrn.edu.br/o/authorize/"
    suap_token_url: str = "https://suap.ifrn.edu.br/o/token/"
    suap_user_info_url: str = "https://suap.ifrn.edu.br/api/rh/meus-dados/"
    suap_identification_url: str = "https://suap.ifrn.edu.br/api/rh/eu/"
    suap_attendance_url: str = (
        "https://suap.ifrn.edu.br/api/ensino/frequencia-periodo-letivo/{ano}/{periodo}"
    )
    # Frequência mínima (%) para aprovar time; ano/período letivo consultados no SUAP
    min_attendance_percent: int = 75
    attendance_year: int | None = None  # None = ano corrente
    attendance_period: int = 1

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    live_ticket_secret_key: str

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Mobile
    mobile_deep_link_scheme: str
    mobile_deep_link_path: str

    # App
    app_name: str = "Intercurso API"
    debug: bool = False


settings = Settings()
