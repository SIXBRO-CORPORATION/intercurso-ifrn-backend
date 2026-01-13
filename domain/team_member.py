from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.abstract_domain import AbstractDomain
from domain.enums.donation_status import DonationStatus
from domain.enums.team_member_role import TeamMemberRole

@dataclass
class TeamMember(AbstractDomain):
    team_id: UUID = None
    user_id: UUID = None
    role: TeamMemberRole = None
    donation_status: DonationStatus = None
    donation_confirmed_at: datetime = None
    donation_confirmed_by: UUID = None
    joined_at: datetime = None
