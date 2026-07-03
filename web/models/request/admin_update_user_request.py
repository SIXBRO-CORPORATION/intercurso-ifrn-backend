from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from domain.enums.user_role import UserRole


class AdminUpdateUserRequest(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, min_length=3, max_length=255)
    email: Optional[EmailStr] = Field(default=None)
    role: Optional[str] = Field(default=None)
    atleta: Optional[bool] = Field(default=None)
    active: Optional[bool] = Field(default=None)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().upper()
        if normalized not in UserRole.__members__:
            valid = ", ".join(UserRole.__members__.keys())
            raise ValueError(f"Papel inválido. Valores aceitos: {valid}")
        return normalized
