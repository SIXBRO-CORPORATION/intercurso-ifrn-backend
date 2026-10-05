from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.modality_gender_mode import ModalityGenderMode


class ModalityConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num_periods: int = Field()
    period_durations_minutes: int = Field()
    score_type: str = Field()
    has_third_place_match: bool = Field()
    metadata: Optional[Any] = Field(default=None)
    points_per_set: Optional[int] = Field(default=None)
    final_set_points: Optional[int] = Field(default=None)
    sets_to_win: Optional[int] = Field(default=None)


class ModalityCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    name: str = Field()
    min_members: int = Field()
    max_members: int = Field()
    gender_mode: ModalityGenderMode = Field()
    min_male_members: Optional[int] = Field(default=None)
    min_female_members: Optional[int] = Field(default=None)
    active: bool = Field()
    configuration: Optional[ModalityConfigurationResponse] = Field(default=None)
    message: str = Field()
