from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.penalty_kick_result import PenaltyKickResult


class MatchPenaltyKickRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field(description="Time que cobrou o pênalti")
    result: PenaltyKickResult = Field(description="GOAL (convertido) ou MISS (perdido)")
    player_id: Optional[UUID] = Field(
        default=None,
        description=(
            "Jogador que cobrou (opcional - a interface de pênaltis do UC015 "
            "não exige seleção de jogador, apenas o time)"
        ),
    )
