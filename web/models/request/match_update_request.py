from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchUpdateRequest(BaseModel):
    """UC012 - Gerenciar Chaveamento (Fluxos Alternativos 1 e 2).

    Todos os campos são opcionais: o monitor pode alterar apenas a data,
    apenas os times, ou ambos em uma única requisição.
    """

    model_config = ConfigDict(from_attributes=True)

    scheduled_date: Optional[datetime] = Field(default=None)
    team1_id: Optional[UUID] = Field(default=None)
    team2_id: Optional[UUID] = Field(default=None)
