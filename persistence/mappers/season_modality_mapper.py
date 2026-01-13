from typing import Optional
from domain.season_modality import SeasonModality
from persistence.model.season_modality_entity import SeasonModalityEntity

class SeasonModalityMapper:
    def to_domain(self, entity: Optional[SeasonModalityEntity]) -> Optional[SeasonModality]:
        if entity is None:
            return None

        return SeasonModality(
            id=entity.id,
            season_id=entity.season_id,
            modality_id=entity.modality_id,
            created_at=entity.created_at
        )

    def to_entity(self, domain: SeasonModality) -> SeasonModalityEntity:
        if domain is None:
            return None

        return SeasonModalityEntity(
            id=domain.id,
            season_id=domain.season_id,
            modality_id=domain.modality_id,
            created_at=domain.created_at
        )