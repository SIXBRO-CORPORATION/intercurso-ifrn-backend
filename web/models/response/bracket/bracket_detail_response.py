from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.bracket.bracket_match_response import BracketMatchResponse
from web.models.response.bracket.bracket_summary_response import BracketSummaryResponse


class BracketGroupTeamResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    team_name: Optional[str] = Field(default=None)
    points: int = Field(default=0)
    wins: int = Field(default=0)
    draws: int = Field(default=0)
    losses: int = Field(default=0)
    goals_for: int = Field(default=0)
    goals_against: int = Field(default=0)
    goals_difference: int = Field(default=0)


class BracketGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: UUID = Field()
    name: str = Field()
    display_order: Optional[int] = Field(default=None)
    teams: List[BracketGroupTeamResponse] = Field(default_factory=list)


class BracketDetailResponse(BracketSummaryResponse):

    configuration: Dict[str, Any] = Field(default_factory=dict)
    groups: List[BracketGroupResponse] = Field(default_factory=list)
    matches: List[BracketMatchResponse] = Field(default_factory=list)
