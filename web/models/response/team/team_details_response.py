from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.team.team_member_response import TeamMemberResponse


class TeamDetailsResponse(BaseModel):
    """UC008/UC009 - Detalhes do time, membros e status de doações."""

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    season_id: Optional[UUID] = Field(default=None)
    modality_id: UUID = Field()
    modality_name: Optional[str] = Field(default=None)
    photo: Optional[str] = Field(default=None)
    status: str = Field()
    owner_id: Optional[UUID] = Field(default=None)
    owner_name: Optional[str] = Field(default=None)
    captain_id: Optional[UUID] = Field(default=None)
    captain_name: Optional[str] = Field(default=None)
    token_active: bool = Field(default=False)
    submmited_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    rejected_at: Optional[datetime] = Field(default=None)
    members: List[TeamMemberResponse] = Field(default_factory=list)
    donations_confirmed: int = Field(default=0)
    donations_total: int = Field(default=0)
