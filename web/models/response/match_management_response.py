from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    photo: Optional[str] = Field(default=None, description="Logo do time")
    score: int = Field(description="Placar atual do time")


class MatchPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field()
    name: str = Field()
    matricula: str = Field()
    role: str = Field()


class MatchModalityConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num_periods: Optional[int] = Field(default=None)
    period_duration_minutes: Optional[int] = Field(default=None)
    score_type: Optional[str] = Field(default=None)
    has_third_place_match: Optional[bool] = Field(default=None)


class MatchTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID = Field()
    event_type: str = Field()
    clock_seconds: int = Field()
    team_id: Optional[UUID] = Field(default=None)
    player_id: Optional[UUID] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)


class MatchManagementResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    modality_id: Optional[UUID] = Field(default=None)
    modality_name: Optional[str] = Field(default=None)
    match_type: str = Field()
    match_category: str = Field()
    status: str = Field()
    scheduled_date: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    monitor_id: Optional[UUID] = Field(default=None)

    team1: MatchTeamResponse = Field()
    team2: MatchTeamResponse = Field()
    team1_players: List[MatchPlayerResponse] = Field(default_factory=list)
    team2_players: List[MatchPlayerResponse] = Field(default_factory=list)

    clock_seconds: int = Field()
    clock_running: bool = Field()
    current_period: int = Field()

    modality_configuration: Optional[MatchModalityConfigurationResponse] = Field(
        default=None
    )

    timeline: List[MatchTimelineEventResponse] = Field(default_factory=list)
