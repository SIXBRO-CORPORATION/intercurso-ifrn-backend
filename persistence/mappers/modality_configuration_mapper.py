from typing import Optional
from domain.modality_configuration import ModalityConfiguration
from domain.enums.score_type import ScoreType
from persistence.model.modality_configuration_entity import ModalityConfigurationEntity

class ModalityConfigurationMapper:
    def to_domain(self, entity: Optional[ModalityConfigurationEntity]) -> Optional[ModalityConfiguration]:
        if entity is None:
            return None

        return ModalityConfiguration(
            id=entity.id,
            season_modality_id=entity.season_modality_id,
            num_periods=entity.num_periods,
            period_durations_minutes=entity.period_durations_minutes,
            score_type=ScoreType(entity.score_type) if entity.score_type else None,
            has_third_place_match=entity.has_third_place_match,
            metadata=entity.metadata,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: ModalityConfiguration) -> ModalityConfigurationEntity:
        if domain is None:
            return None

        return ModalityConfigurationEntity(
            id=domain.id,
            season_modality_id=domain.season_modality_id,
            num_periods=domain.num_periods,
            period_durations_minutes=domain.period_durations_minutes,
            score_type=domain.score_type.value if domain.score_type else None,
            has_third_place_match=domain.has_third_place_match,
            metadata=domain.metadata,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )