from pydantic_settings import BaseSettings, SettingsConfigDict


class MessagingSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""


messaging_settings = MessagingSettings()
