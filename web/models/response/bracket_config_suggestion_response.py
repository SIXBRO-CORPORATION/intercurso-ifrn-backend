from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BracketConfigSuggestionResponse(BaseModel):
    """UC011 - Fluxo principal, passo 7 (sugestão de configuração)."""

    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    format: str = Field()
    team_count: int = Field()
    byes_estimated: int = Field(default=0)
    suggested_configuration: dict = Field(default_factory=dict)
