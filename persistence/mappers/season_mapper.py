from typing import Optional
from domain.season import Season
from domain.enums.season_status import SeasonStatus
from persistence.model.season_entity import SeasonEntity

class SeasonMapper:
    def to_domain(self, entity: Optional[SeasonEntity]) -> Optional[Season]:
        if entity is None:
            return None

        return Season(
            id=entity.id,
            name=entity.name,
            year=entity.year,
            status=SeasonStatus(entity.status) if entity.status else None,
            registration_start_date=entity.registration_start_date,
            registration_end_date=entity.registration_end_date,
            registration_opened_at=entity.registration_opened_at,
            registration_closed_at=entity.registration_closed_at,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            rules_document=entity.rules_document,
            created_by=entity.created_by,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: Season) -> SeasonEntity:
        if domain is None:
            return None

        return SeasonEntity(
            id=domain.id,
            name=domain.name,
            year=domain.year,
            status=domain.status.value if domain.status else None,
            registration_start_date=domain.registration_start_date,
            registration_end_date=domain.registration_end_date,
            registration_opened_at=domain.registration_opened_at,
            registration_closed_at=domain.registration_closed_at,
            started_at=domain.started_at,
            finished_at=domain.finished_at,
            rules_document=domain.rules_document,
            created_by=domain.created_by,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )