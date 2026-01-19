from typing import Optional
from domain.team import Team
from domain.enums.team_status import TeamStatus
from persistence.model.team_entity import TeamEntity


class TeamMapper:
    def to_domain(self, entity: Optional[TeamEntity]) -> Optional[Team]:
        if entity is None:
            return None

        return Team(
            id=entity.id,
            name=entity.name,
            season_id=entity.season_id,
            modality_id=entity.modality_id,
            owner_id=entity.owner_id,
            captain_id=entity.captain_id,
            status=TeamStatus(entity.status) if entity.status else TeamStatus.DRAFT,
            invite_token=str(entity.invite_token) if entity.invite_token else None,
            token_active=entity.token_active,
            photo=entity.photo,
            submmited_at=entity.submitted_at,
            approved_at=entity.approved_at,
            approved_by=entity.approved_by,
            rejected_at=entity.rejected_at,
            rejected_by=entity.rejected_by,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            deleted_at=entity.deleted_at,
            active=entity.active,
        )

    def to_entity(self, domain: Team) -> TeamEntity:
        if domain is None:
            return None

        return TeamEntity(
            id=domain.id,
            name=domain.name,
            season_id=domain.season_id,
            modality_id=domain.modality_id,
            owner_id=domain.owner_id,
            captain_id=domain.captain_id,
            status=domain.status.value if domain.status else TeamStatus.DRAFT.value,
            invite_token=domain.invite_token,
            token_active=domain.token_active,
            photo=domain.photo,
            submitted_at=domain.submmited_at,
            approved_at=domain.approved_at,
            approved_by=domain.approved_by,
            rejected_at=domain.rejected_at,
            rejected_by=domain.rejected_by,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            deleted_at=domain.deleted_at,
            active=domain.active,
        )