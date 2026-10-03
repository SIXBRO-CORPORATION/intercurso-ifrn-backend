from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BracketSummaryResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    bracket_id: UUID = Field()
    season_id: UUID = Field()
    modality_id: UUID = Field()
    modality_name: Optional[str] = Field(default=None)
    format: str = Field()
    status: str = Field()
    total_matches: int = Field(default=0)
    started_matches: int = Field(default=0)
    finished_matches: int = Field(default=0)
    available_actions: List[str] = Field(default_factory=list)
