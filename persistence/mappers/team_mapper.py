from typing import Optional

from domain.team import Team
from persistence.model.team_entity import TeamEntity


class TeamMapper:
    def to_domain(self, entity: Optional[TeamEntity]) -> Optional[Team]:
        if entity is None:
            return None

        return Team(
            id=entity.id,
            name=entity.name,
            photo=entity.photo,
            modality=entity.modality,
            status=entity.status,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active,
        )

    def to_entity(self, team: Team) -> TeamEntity:
        entity = TeamEntity(
            id=team.id,
            name=team.name,
            photo=team.photo,
            modality=team.modality,
            status=team.status,
            created_at=team.created_at,
            modified_at=team.modified_at,
            active=team.active,
        )

        return entity
