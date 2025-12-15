from enum import Enum


class TeamMemberStatus(Enum):
    PENDING_DONATION = "Aguardando doação"
    DONATION_CONFIRMED = "Doação confirmada"