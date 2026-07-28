from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SeasonEditDatesRequest(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    new_registration_start_date: Optional[datetime] = Field(default=None)
    new_registration_end_date: Optional[datetime] = Field(default=None)
    reason: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_at_least_one_date(self) -> "SeasonEditDatesRequest":
        if (
            self.new_registration_start_date is None
            and self.new_registration_end_date is None
        ):
            raise ValueError(
                "Informe ao menos uma data para atualizar (abertura e/ou encerramento)"
            )
        return self
