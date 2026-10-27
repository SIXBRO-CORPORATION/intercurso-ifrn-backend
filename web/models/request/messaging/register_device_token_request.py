from pydantic import BaseModel, Field, field_validator

from domain.enums.device_platform import DevicePlatform


class RegisterDeviceTokenRequest(BaseModel):
    token: str = Field(
        min_length=10, max_length=500, description="Token do FCM do dispositivo"
    )
    platform: str = Field(description="ANDROID ou IOS")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Token não pode ser vazio")
        return v.strip()

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        normalized = (v or "").strip().upper()
        if normalized not in DevicePlatform.__members__:
            raise ValueError("Plataforma inválida. Valores aceitos: ANDROID, IOS")
        return normalized
