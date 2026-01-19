from typing import Optional
from domain.bracket_group import BracketGroup
from persistence.model.bracket_group_entity import BracketGroupEntity

class BracketGroupMapper:
    def to_domain(self, entity: Optional[BracketGroupEntity]) -> Optional[BracketGroup]:
        if entity is None:
            return None

        return BracketGroup(
            id=entity.id,
            bracket_id=entity.bracket_id,
            name=entity.name,
            display_order=entity.display_order,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: BracketGroup) -> BracketGroupEntity:
        if domain is None:
            return None

        return BracketGroupEntity(
            id=domain.id,
            bracket_id=domain.bracket_id,
            name=domain.name,
            display_order=domain.display_order,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )