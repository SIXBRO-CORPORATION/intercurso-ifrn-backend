from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from domain.enums.user_role import UserRole


class AdminCreateUserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=3, max_length=255)
    email: Optional[EmailStr] = Field(default=None)
    cpf: int = Field()
    matricula: int = Field()
    role: str = Field(description="MONITOR ou ADMIN")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        normalized = (v or "").strip().upper()
        if normalized == UserRole.USER.name:
            raise ValueError(
                "Não é possível criar usuários com papel USER por aqui — "
                "esse papel é atribuído automaticamente no primeiro login via SUAP"
            )
        if normalized not in UserRole.__members__:
            raise ValueError("Papel inválido. Valores aceitos: MONITOR, ADMIN")
        return normalized

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()
