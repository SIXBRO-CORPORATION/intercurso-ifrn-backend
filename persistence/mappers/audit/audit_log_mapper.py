from typing import Optional

from domain.audit.audit_log import AuditLog
from domain.enums.audit_action import AuditAction
from persistence.model.audit.audit_log_entity import AuditLogEntity


class AuditLogMapper:
    def to_domain(self, entity: Optional[AuditLogEntity]) -> Optional[AuditLog]:
        if entity is None:
            return None

        return AuditLog(
            id=entity.id,
            actor_id=entity.actor_id,
            actor_role=entity.actor_role,
            action=AuditAction(entity.action) if entity.action else None,
            description=entity.description,
            created_at=entity.created_at,
        )

    def to_entity(self, domain: AuditLog) -> AuditLogEntity:
        if domain is None:
            return None

        return AuditLogEntity(
            id=domain.id,
            actor_id=domain.actor_id,
            actor_role=domain.actor_role,
            action=domain.action.value if domain.action else None,
            description=domain.description,
            created_at=domain.created_at,
        )