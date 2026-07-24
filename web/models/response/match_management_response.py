from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    photo: Optional[str] = Field(default=None, description="Logo do time")
    score: int = Field(description="Placar atual do time (no vôlei, placar do set em andamento)")
    sets_won: Optional[int] = Field(
        default=None,
        description="Sets vencidos na partida (apenas modalidades com score_type SETS)",
    )


class MatchSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    set_number: int = Field()
    team1_points: int = Field()
    team2_points: int = Field()
    winner_team_id: UUID = Field()


class MatchPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field()
    name: str = Field()
    matricula: str = Field()
    role: str = Field()


class MatchModalityConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num_periods: Optional[int] = Field(default=None)
    period_duration_minutes: Optional[int] = Field(default=None)
    score_type: Optional[str] = Field(default=None)
    has_third_place_match: Optional[bool] = Field(default=None)
    points_per_set: Optional[int] = Field(
        default=None, description="Vôlei (ADR002): pontos necessários para vencer um set normal"
    )
    final_set_points: Optional[int] = Field(
        default=None, description="Vôlei (ADR002): pontos necessários para vencer o set decisivo"
    )
    sets_to_win: Optional[int] = Field(
        default=None, description="Vôlei (ADR002): sets necessários para vencer a partida"
    )


class MatchTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID = Field()
    event_type: str = Field()
    clock_seconds: int = Field()
    team_id: Optional[UUID] = Field(default=None)
    player_id: Optional[UUID] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    metadata: Optional[Any] = Field(
        default=None,
        description=(
            "Dados adicionais do evento (ex: cartões anteriores em CARD_YELLOW, "
            "motivo da EXPULSION, placar do set em SET_END)"
        ),
    )


class MatchManagementResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field()
    bracket_id: UUID = Field()
    modality_id: Optional[UUID] = Field(default=None)
    modality_name: Optional[str] = Field(default=None)
    match_type: str = Field()
    match_category: str = Field()
    status: str = Field()
    scheduled_date: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    monitor_id: Optional[UUID] = Field(default=None)

    team1: MatchTeamResponse = Field()
    team2: MatchTeamResponse = Field()
    team1_players: List[MatchPlayerResponse] = Field(default_factory=list)
    team2_players: List[MatchPlayerResponse] = Field(default_factory=list)

    clock_seconds: int = Field()
    clock_running: bool = Field()
    current_period: int = Field()

    modality_configuration: Optional[MatchModalityConfigurationResponse] = Field(
        default=None
    )

    timeline: List[MatchTimelineEventResponse] = Field(default_factory=list)

    sets: List[MatchSetResponse] = Field(
        default_factory=list,
        description="Histórico de sets já disputados (vôlei, ADR002); vazio para outras modalidades",
    )

    metadata: Optional[Any] = Field(
        default=None,
        description=(
            "Metadados livres da partida (uso genérico/futuro). Os dados de "
            "sets do vôlei NÃO ficam mais aqui: veja team1.sets_won/"
            "team2.sets_won e o campo `sets` (ADR002)."
        ),
    )
    match_point_reached: Optional[bool] = Field(
        default=None,
        description=(
            "Preenchido apenas na resposta de "
            "fim de set, indica se algum time já atingiu os sets necessários "
            "para vencer a partida (sugestão para UC015)"
        ),
    )
