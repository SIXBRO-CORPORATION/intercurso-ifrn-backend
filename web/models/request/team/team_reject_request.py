from pydantic import BaseModel, Field


class TeamRejectRequest(BaseModel):

    reason: str = Field(min_length=1, max_length=500)
