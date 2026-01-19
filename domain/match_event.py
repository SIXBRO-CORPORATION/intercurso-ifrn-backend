from dataclasses import dataclass, field
from uuid import UUID

from domain.abstract_domain import AbstractDomain
from domain.enums.event_type import EventType


@dataclass
class MatchEvent(AbstractDomain):
    match_id: UUID = None
    team_id: UUID = None
    player_id:UUID = None
    event_type: EventType = None
    clock_seconds: int = None
    metadata: dict = field(default_factory=dict)
