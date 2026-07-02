from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModalityCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    name: str = Field()
    min_members: int = Field()
    max_members: int = Field()
    active: bool = Field()
    message: str = Field()
