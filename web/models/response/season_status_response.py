from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonStatusResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    season_id: UUID = Field()
    name: str = Field()
    status: str = Field()
    active: bool = Field()
    registration_start_date: Optional[datetime] = Field(default=None)
    registration_end_date: Optional[datetime] = Field(default=None)
    registration_closed_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    message: str = Field()
