from datetime import datetime
from pydantic import BaseModel, Field

from web.models.response.user_response import UserResponse


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token (curta duração)")

    refresh_token: str = Field(..., description="Refresh token (longa duração)")

    token_type: str = Field(
        default="bearer", description="Tipo do token (sempre 'bearer')"
    )

    expires_at: datetime = Field(
        ..., description="Data/hora de expiração do access token"
    )

    user: UserResponse = Field(..., description="Dados do usuário autenticado")
