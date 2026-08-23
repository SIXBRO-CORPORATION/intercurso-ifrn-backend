from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamSummaryResponse(BaseModel):
    """UC005 - Listagem de times do aluno / UC009 - Listar Times Pendentes."""

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    season_id: Optional[UUID] = Field(default=None)
    modality_id: UUID = Field()
    modality_name: Optional[str] = Field(default=None)
    status: str = Field()
    owner_id: Optional[UUID] = Field(default=None)
    owner_name: Optional[str] = Field(default=None)
    members_count: int = Field(default=0)
    donations_confirmed: int = Field(default=0)
    donations_total: int = Field(default=0)
    submmited_at: Optional[datetime] = Field(default=None)
