from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.modality_gender_mode import ModalityGenderMode


class ModalitySummaryResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    name: str = Field()
    min_members: int = Field()
    max_members: int = Field()
    gender_mode: ModalityGenderMode = Field()
    min_male_members: Optional[int] = Field(default=None)
    min_female_members: Optional[int] = Field(default=None)
