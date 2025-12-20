from pydantic import BaseModel, Field
from datetime import datetime

class TokenRefreshResponse(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    token_type: str = Field(default="bearer")
    expires_at: datetime = Field(...)