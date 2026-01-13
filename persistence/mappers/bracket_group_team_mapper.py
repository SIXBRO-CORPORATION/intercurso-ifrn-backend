from typing import Optional
from domain.bracket_group_team import BracketGroupTeam
from persistence.model.bracket_group_team_entity import BracketGroupTeamEntity

class BracketGroupTeamMapper:
    def to_domain(self, entity: Optional[BracketGroupTeamEntity]) -> Optional[BracketGroupTeam]:
        if entity is None:
            return None

        return BracketGroupTeam(
            id=entity.id,
            bracket_group_id=entity.bracket_group_id,
            team_id=entity.team_id,
            points=entity.points,
            wins=entity.wins,
            draws=entity.draws,
            losses=entity.losses,
            goals_for=entity.goals_for,
            goals_against=entity.goals_against,
            goals_difference=entity.goals_difference,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: BracketGroupTeam) -> BracketGroupTeamEntity:
        if domain is None:
            return None

        return BracketGroupTeamEntity(
            id=domain.id,
            bracket_group_id=domain.bracket_group_id,
            team_id=domain.team_id,
            points=domain.points,
            wins=domain.wins,
            draws=domain.draws,
            losses=domain.losses,
            goals_for=domain.goals_for,
            goals_against=domain.goals_against,
            goals_difference=domain.goals_difference,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )