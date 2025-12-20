from pydantic import BaseModel, Field, field_validator


class TeamMemberRequest(BaseModel):
    matricula: int = Field()
    name: str = Field()
    cpf: str = Field()
