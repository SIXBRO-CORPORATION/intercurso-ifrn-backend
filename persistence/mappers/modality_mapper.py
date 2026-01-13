from typing import Optional
from domain.modality import Modality
from persistence.model.modality_entity import ModalityEntity

class ModalityMapper:
    def to_domain(self, entity: Optional[ModalityEntity]) -> Optional[Modality]:
        if entity is None:
            return None

        return Modality(
            id=entity.id,
            name=entity.name,
            min_members=entity.min_members,
            max_members=entity.max_members,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: Modality) -> ModalityEntity:
        if domain is None:
            return None

        return ModalityEntity(
            id=domain.id,
            name=domain.name,
            min_members=domain.min_members,
            max_members=domain.max_members,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )