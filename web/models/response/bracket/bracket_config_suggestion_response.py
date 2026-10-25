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
    total_matches_estimated: int = Field(
        default=0,
        description=(
            "Quantidade de partidas que o sorteio vai gerar, sem contar a disputa "
            "de terceiro lugar (exibida separadamente via suggested_configuration."
            "has_third_place)."
        ),
    )
    matches_by_round: list[int] = Field(
        default_factory=list,
        description=(
            "Quantidade de partidas por rodada/turno, da primeira até a última, "
            "na mesma ordem em que seriam exibidas (ex.: [4, 2, 1] para um "
            "mata-mata de 8 times)."
        ),
    )
