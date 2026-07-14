from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BracketResponse(BaseModel):
    """UC011/UC012 - Bloco de Dados 2 (Chaveamento Criado)."""

    model_config = ConfigDict(from_attributes=True)

    bracket_id: UUID = Field()
    season_id: UUID = Field()
    modality_id: UUID = Field()
    format: str = Field()
    configuration: dict = Field(default_factory=dict)
    status: str = Field()
    teams_count: int = Field()
    groups_created: int = Field(default=0)
    matches_created: int = Field()
    byes_created: int = Field(default=0)
    season_transitioned_to_in_progress: bool = Field(default=False)
