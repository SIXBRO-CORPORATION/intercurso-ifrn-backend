from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.match.match_management_response import MatchManagementResponse


class MatchPublicPlayerResponse(BaseModel):
    """UC016 / ADR 0004: jogador em schema público — nunca inclui matricula."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field()
    name: str = Field()
    role: str = Field()


class MatchPublicResponse(MatchManagementResponse):
    """GET público e payload SSE (ADR 0004, Princípio 1): mesmo conteúdo de
    MatchManagementResponse, mas os jogadores nunca trazem `matricula`."""

    team1_players: List[MatchPublicPlayerResponse] = Field(default_factory=list)
    team2_players: List[MatchPublicPlayerResponse] = Field(default_factory=list)
