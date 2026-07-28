from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchResponse(BaseModel):
    """UC012 - Bloco de Dados 2 (Partida para Edição)."""

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    team1_id: Optional[UUID] = Field(default=None)
    team2_id: Optional[UUID] = Field(default=None)
    scheduled_date: Optional[datetime] = Field(default=None)
    status: str = Field()
    match_type: str = Field()
    match_category: str = Field()
