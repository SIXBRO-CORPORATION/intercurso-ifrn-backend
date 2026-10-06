from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    r2_endpoint_url: str = ""
    r2_presigned_url_expires_seconds: int = 3600


storage_settings = StorageSettings()
