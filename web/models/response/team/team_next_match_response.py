from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeamNextMatchTeamResponse(BaseModel):
    team_id: UUID = Field()
    name: str = Field()
    photo: Optional[str] = Field(default=None)


class TeamNextMatchResponse(BaseModel):

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    group_name: Optional[str] = Field(
        default=None, description="Rodada/fase do chaveamento, ex. 'Quartas de final'"
    )
    match_type: str = Field()
    status: str = Field()
    scheduled_date: Optional[datetime] = Field(default=None)
    team1: Optional[TeamNextMatchTeamResponse] = Field(default=None)
    team2: Optional[TeamNextMatchTeamResponse] = Field(default=None)
