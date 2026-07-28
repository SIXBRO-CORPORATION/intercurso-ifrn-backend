from dataclasses import dataclass
from uuid import UUID

from domain.abstract_domain import AbstractDomain


@dataclass
class MatchSet(AbstractDomain):
    match_id: UUID = None
    set_number: int = None
    team1_points: int = None
    team2_points: int = None
    winner_team_id: UUID = None
