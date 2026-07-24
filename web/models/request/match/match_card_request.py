from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.card_type import CardType


class MatchCardRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field(description="Time do jogador")
    player_id: UUID = Field(description="Jogador que recebeu o cartão (obrigatório)")
    card_type: CardType = Field(description="YELLOW ou RED")
