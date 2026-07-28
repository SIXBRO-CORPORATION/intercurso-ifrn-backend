from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SeasonCreateRequest(BaseModel):
    """UC001 - Criar Temporada.

    `registration_start_date` é opcional apenas quando `open_immediately`
    é True (nesse caso o sistema usa a data/hora atual como abertura).
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    year: int = Field()
    modality_ids: List[UUID] = Field(min_length=1)
    registration_start_date: Optional[datetime] = Field(default=None)
    registration_end_date: datetime = Field()
    open_immediately: bool = Field(default=False)
    rules_document: Optional[str] = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome da temporada não pode ser vazio")
        return v.strip()
