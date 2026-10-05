from typing import Optional
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.modality.modality import Modality
from persistence.model.modality.modality_entity import ModalityEntity

class ModalityMapper:
    def to_domain(self, entity: Optional[ModalityEntity]) -> Optional[Modality]:
        if entity is None:
            return None

        return Modality(
            id=entity.id,
            name=entity.name,
            min_members=entity.min_members,
            max_members=entity.max_members,
            gender_mode=ModalityGenderMode(entity.gender_mode) if entity.gender_mode else None,
            min_male_members=entity.min_male_members,
            min_female_members=entity.min_female_members,
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
            gender_mode=domain.gender_mode.value if domain.gender_mode else None,
            min_male_members=domain.min_male_members,
            min_female_members=domain.min_female_members,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )
