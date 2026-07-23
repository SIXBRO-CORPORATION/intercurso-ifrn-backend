from dataclasses import dataclass
from datetime import datetime

from domain.abstract_domain import AbstractDomain
from domain.enums.team_status import TeamStatus
from uuid import UUID

@dataclass
class Team(AbstractDomain):
    name: str = None
    season_id: UUID = None
    modality_id: UUID = None
    owner_id: UUID = None
    captain_id: UUID = None
    status: TeamStatus = TeamStatus.DRAFT
    invite_token: str = None
    token_active: bool = True
    photo: str = None
    submmited_at: datetime = None
    approved_at: datetime = None
    approved_by: UUID = None
    rejected_at: datetime = None
    rejected_by: UUID = None
