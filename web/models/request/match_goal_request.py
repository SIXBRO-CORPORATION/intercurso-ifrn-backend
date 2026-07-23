from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchGoalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field(description="Time que marcou")
    player_id: UUID = Field(description="Jogador que marcou (obrigatório)")
