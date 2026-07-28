from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums.score_type import ScoreType


class ModalityCreateRequest(BaseModel):
    """UC004 - Cadastrar Modalidade."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    min_members: int = Field(ge=1)
    max_members: int = Field(ge=1)

    # Bloco de Dados 2 - Configuração de Partida da Modalidade
    num_periods: int = Field(ge=1)
    period_durations_minutes: int = Field(ge=1)
    score_type: ScoreType = Field()
    has_third_place_match: bool = Field(default=False)
    metadata: Optional[Any] = Field(default=None)

    # ADR 0002 - configuração específica do vôlei (obrigatória quando
    # score_type == SETS; validado no adapter de negócio, não aqui).
    points_per_set: Optional[int] = Field(default=None, ge=1)
    final_set_points: Optional[int] = Field(default=None, ge=1)
    sets_to_win: Optional[int] = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome da modalidade não pode ser vazio")
        return v.strip()
