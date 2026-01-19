from typing import Optional
from domain.bracket import Bracket
from domain.enums.modality_format import ModalityFormat
from domain.enums.bracket_status import BracketStatus
from persistence.model.bracket_entity import BracketEntity

class BracketMapper:
    def to_domain(self, entity: Optional[BracketEntity]) -> Optional[Bracket]:
        if entity is None:
            return None

        return Bracket(
            id=entity.id,
            season_id=entity.season_id,
            modality_id=entity.modality_id,
            format=ModalityFormat(entity.format) if entity.format else None,
            configuration=entity.configuration,
            status=BracketStatus(entity.status) if entity.status else None,
            created_by=entity.created_by,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: Bracket) -> BracketEntity:
        if domain is None:
            return None

        return BracketEntity(
            id=domain.id,
            season_id=domain.season_id,
            modality_id=domain.modality_id,
            format=domain.format.value if domain.format else None,
            configuration=domain.configuration,
            status=domain.status.value if domain.status else None,
            created_by=domain.created_by,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )