from typing import Optional

from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)
from persistence.model.volleyball_modality_configuration_entity import (
    VolleyballModalityConfigurationEntity,
)


class VolleyballModalityConfigurationMapper:
    def to_domain(
        self, entity: Optional[VolleyballModalityConfigurationEntity]
    ) -> Optional[VolleyballModalityConfiguration]:
        if entity is None:
            return None

        return VolleyballModalityConfiguration(
            id=entity.id,
            modality_configuration_id=entity.modality_configuration_id,
            points_per_set=entity.points_per_set,
            final_set_points=entity.final_set_points,
            sets_to_win=entity.sets_to_win,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active,
        )

    def to_entity(
        self, domain: Optional[VolleyballModalityConfiguration]
    ) -> Optional[VolleyballModalityConfigurationEntity]:
        if domain is None:
            return None

        return VolleyballModalityConfigurationEntity(
            id=domain.id,
            modality_configuration_id=domain.modality_configuration_id,
            points_per_set=domain.points_per_set,
            final_set_points=domain.final_set_points,
            sets_to_win=domain.sets_to_win,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active,
        )
