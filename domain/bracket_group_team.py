from dataclasses import dataclass
from uuid import UUID

from domain.abstract_domain import AbstractDomain


@dataclass
class BracketGroupTeam(AbstractDomain):
    bracket_group_id: UUID = None
    team_id: UUID = None
    points: int = None
    wins: int = None
    draws: int = None
    losses: int = None
    goals_for: int = None
    goals_against: int = None
    goals_difference: int = None    