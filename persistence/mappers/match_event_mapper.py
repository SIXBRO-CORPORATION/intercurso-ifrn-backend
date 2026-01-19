from typing import Optional
from domain.match_event import MatchEvent
from domain.enums.event_type import EventType
from persistence.model.match_event_entity import MatchEventEntity

class MatchEventMapper:
    def to_domain(self, entity: Optional[MatchEventEntity]) -> Optional[MatchEvent]:
        if entity is None:
            return None

        return MatchEvent(
            id=entity.id,
            match_id=entity.match_id,
            team_id=entity.team_id,
            player_id=entity.player_id,
            event_type=EventType(entity.event_type) if entity.event_type else None,
            clock_seconds=entity.clock_seconds,
            metadata=entity.metadata,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: MatchEvent) -> MatchEventEntity:
        if domain is None:
            return None

        return MatchEventEntity(
            id=domain.id,
            match_id=domain.match_id,
            team_id=domain.team_id,
            player_id=domain.player_id,
            event_type=domain.event_type.value if domain.event_type else None,
            clock_seconds=domain.clock_seconds,
            metadata=domain.metadata,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )