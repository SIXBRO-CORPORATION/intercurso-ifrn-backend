from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.score_type import ScoreType


class ModalityCreateRequest(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    min_members: int = Field(ge=1)
    max_members: int = Field(ge=1)

    gender_mode: ModalityGenderMode = Field()
    min_male_members: Optional[int] = Field(default=None, ge=0)
    min_female_members: Optional[int] = Field(default=None, ge=0)

    num_periods: int = Field(ge=1)
    period_durations_minutes: int = Field(ge=1)
    score_type: ScoreType = Field()
    has_third_place_match: bool = Field(default=False)
    metadata: Optional[Any] = Field(default=None)

    points_per_set: Optional[int] = Field(default=None, ge=1)
    final_set_points: Optional[int] = Field(default=None, ge=1)
    sets_to_win: Optional[int] = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome da modalidade não pode ser vazio")
        return v.strip()

    @model_validator(mode="after")
    def validate_gender_quotas(self) -> "ModalityCreateRequest":
        if self.gender_mode == ModalityGenderMode.MIXED:
            if self.min_male_members is None or self.min_female_members is None:
                raise ValueError(
                    "min_male_members e min_female_members são obrigatórios "
                    "quando gender_mode é MIXED"
                )
        else:
            if self.min_male_members is not None or self.min_female_members is not None:
                raise ValueError(
                    "min_male_members e min_female_members só são aplicáveis "
                    "quando gender_mode é MIXED"
                )
        return self
