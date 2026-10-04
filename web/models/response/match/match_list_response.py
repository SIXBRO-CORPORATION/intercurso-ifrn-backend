from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.match.match_management_response import MatchTeamResponse


class MatchListItemResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    modality_id: Optional[UUID] = Field(default=None)
    modality_name: Optional[str] = Field(default=None)
    group_name: Optional[str] = Field(default=None)
    match_type: str = Field()
    match_category: str = Field()
    status: str = Field()
    scheduled_date: Optional[datetime] = Field(default=None)
    team1: Optional[MatchTeamResponse] = Field(
        default=None, description="Nulo enquanto o time não está definido (A definir)"
    )
    team2: Optional[MatchTeamResponse] = Field(default=None)
    winner_id: Optional[UUID] = Field(default=None)
    clock_seconds: int = Field()
    clock_running: bool = Field()
    current_period: int = Field()


class MatchListResponse(BaseModel):
    items: List[MatchListItemResponse] = Field()
    total: int = Field()
    page: int = Field()
    size: int = Field()
