from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeamMemberResponse(BaseModel):
    matricula: int = Field()
    name: str = Field()
    cpf: str = Field()
    status: str = Field()
    user_id: Optional[UUID] = Field(default=None)
    is_registered: bool = Field()
