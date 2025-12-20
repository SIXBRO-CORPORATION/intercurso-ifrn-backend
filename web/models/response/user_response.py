from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID = Field()
    name: str = Field()
    email: str = Field()
    matricula: int = Field()
    cpf: int = Field()
    created_at: datetime = Field()
    modified_at: datetime = Field()
    active: bool = Field()
