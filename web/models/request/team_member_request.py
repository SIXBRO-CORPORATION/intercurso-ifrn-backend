from pydantic import BaseModel, Field


class TeamMemberRequest(BaseModel):
    matricula: int = Field()
    name: str = Field()
    cpf: str = Field()
