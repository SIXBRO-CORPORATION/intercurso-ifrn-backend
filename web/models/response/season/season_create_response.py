from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season_id: UUID = Field()
    name: str = Field()
    year: int = Field()
    status: str = Field()
    active: bool = Field()
    registration_start_date: Optional[datetime] = Field(default=None)
    registration_end_date: Optional[datetime] = Field(default=None)
    modality_ids: List[UUID] = Field(default_factory=list)
    message: str = Field()
