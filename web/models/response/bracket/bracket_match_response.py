from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BracketMatchResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    group_name: Optional[str] = Field(default=None)
    team1_id: Optional[UUID] = Field(default=None)
    team1_name: Optional[str] = Field(default=None)
    team2_id: Optional[UUID] = Field(default=None)
    team2_name: Optional[str] = Field(default=None)
    scheduled_date: Optional[datetime] = Field(default=None)
    match_type: str = Field()
    match_category: str = Field()
    status: str = Field()
    round_name: Optional[str] = Field(
        default=None,
        description=(
            "Nome da fase do mata-mata (ex.: 'Oitavas de final'), derivado da "
            "árvore de next_match_id. Ausente para partidas de grupo."
        ),
    )
    round_order: Optional[int] = Field(
        default=None,
        description=(
            "1 = rodada mais distante da final, crescendo em direção a ela. "
            "Ausente para partidas de grupo."
        ),
    )
