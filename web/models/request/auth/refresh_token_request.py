from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ..., description="Refresh token para renovar o access token", min_length=10
    )
