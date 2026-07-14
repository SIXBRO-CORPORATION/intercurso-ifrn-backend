from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums.modality_format import ModalityFormat


class BracketCreateRequest(BaseModel):
    """UC011 - Criar Chaveamento.

    `configuration` é opcional: quando omitida, o sistema calcula a
    configuração sugerida automaticamente (mesma lógica usada no preview
    de `GET /api/bracket/preview`).
    """

    model_config = ConfigDict(from_attributes=True)

    modality_id: UUID = Field()
    format: str = Field()
    configuration: Optional[dict] = Field(default=None)

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        normalized = v.strip().upper()
        if normalized not in ModalityFormat.__members__:
            valid = ", ".join(ModalityFormat.__members__.keys())
            raise ValueError(f"Formato inválido. Valores aceitos: {valid}")
        return normalized

