from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamJoinResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    team_name: str = Field()
    role: str = Field()
    donation_status: str = Field()
    joined_at: datetime = Field()
    message: str = Field()
