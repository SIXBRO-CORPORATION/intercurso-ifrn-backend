from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field()
    name: str = Field()
    email: Optional[str] = Field(default=None)
    matricula: str = Field()
    role: str = Field()
    atleta: bool = Field()
    active: bool = Field()
