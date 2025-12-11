from dataclasses import dataclass
from uuid import UUID

@dataclass
class TeamMembers:

    team_id: UUID
    member_matricula: int
    member_name: str
    member_cpf: int
    active: bool