from dataclasses import dataclass
from uuid import UUID

@dataclass
class TeamMember:

    team_id: UUID
    user_id: UUID
    member_matricula: int
    member_name: str
    member_cpf: str
    active: bool