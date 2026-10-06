import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TEAM_PHOTO_OBJECT_KEY_PATTERN = re.compile(
    r"^teams/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\.(png|jpg|jpeg)$"
)


class TeamRegisterRequest(BaseModel):

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

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not _TEAM_PHOTO_OBJECT_KEY_PATTERN.match(v):
            raise ValueError(
                "Foto do time deve ser o `object_key` retornado por "
                "POST /api/storage/team-photo, não uma URL nem o conteúdo do arquivo"
            )
        return v
