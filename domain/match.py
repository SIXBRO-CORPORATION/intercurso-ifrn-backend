from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domain.abstract_domain import AbstractDomain
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType


@dataclass
class Match(AbstractDomain):

    bracket_id: UUID = None
    bracket_group_id: UUID = None
    team1_id: UUID = None
    team2_id: UUID = None
    match_type: MatchType = None
    match_category: MatchCategory = None
    status: MatchStatus = None
    scheduled_date: datetime = None
    started_at: datetime = None
    finished_at: datetime = None
    team1_score: int = None
    team2_score: int = None
    penality_result: dict = field(default_factory=dict)
    winner_id: UUID = None
    clock_seconds: int = None
    clock_running: bool = None
    current_period: int = None
    is_bye: bool = None
    metadata: dict = field(default_factory=dict)
