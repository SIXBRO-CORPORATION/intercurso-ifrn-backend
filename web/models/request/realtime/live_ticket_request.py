from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LiveChannelType(str, Enum):
    MATCH = "match"
    SEASON = "season"


class LiveTicketRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_type: LiveChannelType = Field(
        description="Tipo de canal de tempo real: 'match' ou 'season'"
    )
    channel_id: UUID = Field(
        description="Id do recurso (match_id ou season_id) que será assinado"
    )
