from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.team_member_response import TeamMemberResponse


class TeamRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    modality: str = Field()
    status: str = Field()
    photo: Optional[str] = Field()
    members_count: int = Field()
    members: List[TeamMemberResponse] = Field()
    message: str = Field()
