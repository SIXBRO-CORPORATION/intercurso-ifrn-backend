from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.modality_gender_mode import ModalityGenderMode


class ModalitySummaryResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    name: str = Field()
    min_members: int = Field()
    max_members: int = Field()
    gender_mode: ModalityGenderMode = Field()
    min_male_members: Optional[int] = Field(default=None)
    min_female_members: Optional[int] = Field(default=None)
    active: bool = Field(description="Estado atual da modalidade (ativa/inativa)")
    num_periods: Optional[int] = Field(
        default=None, description="Número de períodos/tempos da partida"
    )
    period_durations_minutes: Optional[int] = Field(
        default=None, description="Duração de cada período, em minutos"
    )
    score_type: Optional[str] = Field(
        default=None, description="Sistema de pontuação: GOALS, POINTS ou SETS"
    )
    points_per_set: Optional[int] = Field(
        default=None, description="Pontos por set (apenas score_type=SETS)"
    )
    final_set_points: Optional[int] = Field(
        default=None, description="Pontos do set final (apenas score_type=SETS)"
    )
    sets_to_win: Optional[int] = Field(
        default=None, description="Sets necessários para vencer (apenas score_type=SETS)"
    )
