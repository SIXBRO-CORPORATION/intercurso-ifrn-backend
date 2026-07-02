from uuid import UUID

from pydantic import BaseModel, Field


class TeamMemberResponse(BaseModel):
    user_id: UUID = Field()
    name: str = Field()
    matricula: int = Field()
    role: str = Field()
    donation_status: str = Field()
