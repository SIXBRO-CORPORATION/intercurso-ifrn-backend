from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModalityCreateRequest(BaseModel):
    """UC004 - Cadastrar Modalidade."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    min_members: int = Field(ge=1)
    max_members: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome da modalidade não pode ser vazio")
        return v.strip()
