from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModalityStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    name: str = Field()
    active: bool = Field()
    message: str = Field()
