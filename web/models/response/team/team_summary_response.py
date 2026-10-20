from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamSummaryResponse(BaseModel):
    """UC005 - Listagem de times do aluno / UC009 - Listar Times Pendentes."""

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
    captain_id: Optional[UUID] = Field(
        default=None,
        description=(
            "Permite ao front distinguir Dono/Capitão/Membro (hoje o papel "
            "exibido era binário por falta deste campo — ver "
            "docs/qa/a04-minhas-equipes-criar-equipe.md, Fase 1, achado #2)."
        ),
    )
    max_members: Optional[int] = Field(
        default=None,
        description=(
            "Limite de membros da modalidade do time, já carregado no "
            "backend ao montar a listagem — evita uma segunda chamada de "
            "rede do front só para isso (ver achado de Fase 2 #1 do mesmo "
            "relatório)."
        ),
    )
    members_count: int = Field(default=0)
    donations_confirmed: int = Field(default=0)
    donations_total: int = Field(default=0)
    submmited_at: Optional[datetime] = Field(default=None)
