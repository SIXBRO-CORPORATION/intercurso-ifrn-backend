from typing import Optional
from domain.match import Match
from domain.enums.match_type import MatchType
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from persistence.model.match_entity import MatchEntity

class MatchMapper:
    def to_domain(self, entity: Optional[MatchEntity]) -> Optional[Match]:
        if entity is None:
            return None

        return Match(
            id=entity.id,
            bracket_id=entity.bracket_id,
            bracket_group_id=entity.bracket_group_id,
            team1_id=entity.team1_id,
            team2_id=entity.team2_id,
            match_type=MatchType(entity.match_type) if entity.match_type else None,
            match_category=MatchCategory(entity.match_category) if entity.match_category else None,
            status=MatchStatus(entity.status) if entity.status else None,
            scheduled_date=entity.scheduled_date,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            team1_score=entity.team1_score,
            team2_score=entity.team2_score,
            penality_result=entity.penality_result,
            winner_id=entity.winner_id,
            clock_seconds=entity.clock_seconds,
            clock_running=entity.clock_running,
            current_period=entity.current_period,
            is_bye=entity.is_bye,
            metadata=entity.metadata,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: Match) -> MatchEntity:
        if domain is None:
            return None

        return MatchEntity(
            id=domain.id,
            bracket_id=domain.bracket_id,
            bracket_group_id=domain.bracket_group_id,
            team1_id=domain.team1_id,
            team2_id=domain.team2_id,
            match_type=domain.match_type.value if domain.match_type else None,
            match_category=domain.match_category.value if domain.match_category else None,
            status=domain.status.value if domain.status else None,
            scheduled_date=domain.scheduled_date,
            started_at=domain.started_at,
            finished_at=domain.finished_at,
            team1_score=domain.team1_score,
            team2_score=domain.team2_score,
            penality_result=domain.penality_result,
            winner_id=domain.winner_id,
            clock_seconds=domain.clock_seconds,
            clock_running=domain.clock_running,
            current_period=domain.current_period,
            is_bye=domain.is_bye,
            metadata=domain.metadata,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )