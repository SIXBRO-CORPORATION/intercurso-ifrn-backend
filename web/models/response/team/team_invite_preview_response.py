from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamInvitePreviewResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    modality_id: UUID = Field()
    modality_name: Optional[str] = Field(default=None)
    photo: Optional[str] = Field(default=None)
    members_count: int = Field()
    max_members: Optional[int] = Field(default=None)
    captain_name: Optional[str] = Field(default=None)
    owner_name: Optional[str] = Field(default=None)
