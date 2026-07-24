from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonDetailsResponse(BaseModel):
    """UC002 - Bloco de Dados 1 (Detalhes da Temporada)."""

    model_config = ConfigDict(from_attributes=True)

    season_id: UUID = Field()
    name: str = Field()
    year: int = Field()
    status: str = Field()
    active: bool = Field()
    modality_ids: List[UUID] = Field(default_factory=list)
    registration_start_date: Optional[datetime] = Field(default=None)
    registration_end_date: Optional[datetime] = Field(default=None)
    registration_opened_at: Optional[datetime] = Field(default=None)
    registration_closed_at: Optional[datetime] = Field(default=None)
    total_teams_created: int = Field(default=0)
    total_teams_submitted: int = Field(default=0)
    total_teams_approved: int = Field(default=0)
    available_actions: List[str] = Field(default_factory=list)
