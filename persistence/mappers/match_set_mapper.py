from typing import Optional

from domain.match.match_set import MatchSet
from persistence.model.match_set_entity import MatchSetEntity


class MatchSetMapper:
    def to_domain(self, entity: Optional[MatchSetEntity]) -> Optional[MatchSet]:
        if entity is None:
            return None

        return MatchSet(
            id=entity.id,
            match_id=entity.match_id,
            set_number=entity.set_number,
            team1_points=entity.team1_points,
            team2_points=entity.team2_points,
            winner_team_id=entity.winner_team_id,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active,
        )

    def to_entity(self, domain: Optional[MatchSet]) -> Optional[MatchSetEntity]:
        if domain is None:
            return None

        return MatchSetEntity(
            id=domain.id,
            match_id=domain.match_id,
            set_number=domain.set_number,
            team1_points=domain.team1_points,
            team2_points=domain.team2_points,
            winner_team_id=domain.winner_team_id,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active,
        )
