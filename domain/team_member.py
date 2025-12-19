from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from domain.enums.team_member_status import TeamMemberStatus


@dataclass
class TeamMember:
    team_id: UUID
    user_id: Optional[UUID]
    member_matricula: int
    member_name: str
    member_cpf: str
    status: TeamMemberStatus
