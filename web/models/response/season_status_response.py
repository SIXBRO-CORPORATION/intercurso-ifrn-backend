from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonStatusResponse(BaseModel):
    """Resposta compartilhada pelas operações de edição de datas,
    encerramento antecipado e reabertura de inscrições (UC002)."""

    model_config = ConfigDict(from_attributes=True)

    season_id: UUID = Field()
    name: str = Field()
    status: str = Field()
    active: bool = Field()
    registration_start_date: Optional[datetime] = Field(default=None)
    registration_end_date: Optional[datetime] = Field(default=None)
    registration_closed_at: Optional[datetime] = Field(default=None)
    message: str = Field()
