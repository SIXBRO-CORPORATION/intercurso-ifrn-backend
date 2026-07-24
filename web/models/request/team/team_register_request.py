from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeamRegisterRequest(BaseModel):
    """UC005 - Criar Equipe.

    O time e criado apenas pelo aluno-dono (owner); os demais membros
    entram posteriormente via convite (UC006), portanto nenhuma lista de
    membros e aceita neste request.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=3, max_length=255)
    photo: Optional[str] = Field(default=None)
    modality_id: UUID = Field()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome do time não pode ser vazio")
        return v.strip()
