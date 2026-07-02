from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    modality_id: UUID = Field()
    status: str = Field()
    photo: Optional[str] = Field(default=None)
    invite_token: Optional[str] = Field(default=None)
    owner_id: UUID = Field()
    message: str = Field()
