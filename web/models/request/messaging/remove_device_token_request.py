from pydantic import BaseModel, Field, field_validator


class RemoveDeviceTokenRequest(BaseModel):
    token: str = Field(
        min_length=10, max_length=500, description="Token do FCM a ser removido"
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Token não pode ser vazio")
        return v.strip()
