from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums.modality import ModalityType
from web.models.request.team_member_request import TeamMemberRequest


class TeamRegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=3, max_length=255)
    photo: Optional[str] = Field(default=None)
    modality: ModalityType = Field()
    members: List[TeamMemberRequest] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Nome do time não pode ser vazio")
        return v.strip()

    @field_validator("members")
    @classmethod
    def validate_members_unique(
        cls, v: List[TeamMemberRequest]
    ) -> List[TeamMemberRequest]:
        matriculas = [member.matricula for member in v]
        if len(matriculas) != len(set(matriculas)):
            raise ValueError(
                "Não é permitido membros com matrículas duplicadas no mesmo time"
            )

        cpfs = [member.cpf for member in v]
        if len(cpfs) != len(set(cpfs)):
            raise ValueError(
                "Não é permitido membros com CPFs duplicados no mesmo time"
            )

        return v
