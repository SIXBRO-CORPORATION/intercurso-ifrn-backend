from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from web.models.response.team.team_member_response import TeamMemberResponse
from web.models.response.team.team_next_match_response import TeamNextMatchResponse


class TeamDetailsResponse(BaseModel):
    """UC008/UC009 - Detalhes do time, membros e status de doações."""

    model_config = ConfigDict(from_attributes=True)

    team_id: UUID = Field()
    name: str = Field()
    season_id: Optional[UUID] = Field(default=None)
    modality_id: UUID = Field()
    modality_name: Optional[str] = Field(default=None)
    photo: Optional[str] = Field(default=None)
    status: str = Field()
    owner_id: Optional[UUID] = Field(default=None)
    owner_name: Optional[str] = Field(default=None)
    captain_id: Optional[UUID] = Field(default=None)
    captain_name: Optional[str] = Field(default=None)
    token_active: bool = Field(default=False)
    submmited_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    rejected_at: Optional[datetime] = Field(default=None)
    members: List[TeamMemberResponse] = Field(default_factory=list)
    donations_confirmed: int = Field(default=0)
    donations_total: int = Field(default=0)
    rejection_reason: Optional[str] = Field(default=None)
    invite_token: Optional[str] = Field(default=None, description="Somente para o dono e monitores")
    min_members: Optional[int] = Field(default=None)
    max_members: Optional[int] = Field(default=None)
    gender_mode: Optional[str] = Field(default=None)
    min_male_members: Optional[int] = Field(default=None)
    min_female_members: Optional[int] = Field(default=None)
    can_submit: bool = Field(
        default=False,
        description=(
            "Reflete a mesma regra de elegibilidade usada em PATCH /team/{id}/submit "
            "(temporada ativa, janela de inscrição, cota mínima e de gênero), para o "
            "front não precisar replicá-la."
        ),
    )
    submit_blocked_reason: Optional[str] = Field(
        default=None,
        description="Motivo pelo qual can_submit é falso, só quando o time está em DRAFT",
    )
    can_approve: bool = Field(
        default=False,
        description=(
            "Reflete a mesma regra de elegibilidade usada em PATCH /team/{id}/approve "
            "(membros, doações confirmadas, frequência mínima e cota de gênero), para o "
            "front não precisar replicá-la nem ficar desatualizado em relação a ela."
        ),
    )
    approve_blocked_reason: Optional[str] = Field(
        default=None,
        description="Motivo pelo qual can_approve é falso, só quando o time está em SUBMITTED",
    )
    next_match: Optional[TeamNextMatchResponse] = Field(default=None)
