from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from core.persistence.audit.audit_log_repository_port import AuditLogRepositoryPort
from domain.audit.audit_log import AuditLog
from domain.enums.audit_action import AuditAction


class AuditLogger:
    """Serviço de domínio para registro de auditoria.

    Não é um caso de uso próprio: é injetado nos adapters de negócio que
    precisam registrar auditoria, encapsulando a criação/persistência do
    AuditLog. Quem monta `actor_role` é o adapter (buscando o User via
    UserRepositoryPort), pois o papel deve ser o snapshot do momento da
    ação — nunca um JOIN com a tabela users, já que o papel do usuário
    pode mudar depois e o log precisa refletir o papel que ele tinha
    quando agiu.
    """

    def __init__(self, audit_log_repository: AuditLogRepositoryPort):
        self.audit_log_repository = audit_log_repository

    async def log(
        self,
        action: AuditAction,
        description: str,
        actor_id: Optional[UUID] = None,
        actor_role: Optional[str] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        return await self.audit_log_repository.save(audit_log)