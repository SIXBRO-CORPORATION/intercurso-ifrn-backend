from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from core.persistence.audit.audit_log_repository_port import AuditLogRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.audit.audit_log import AuditLog
from domain.enums.audit_action import AuditAction
from domain.user.user import User


class AuditLogger:
    """Serviço de domínio para registro de auditoria.

    Não é um caso de uso próprio: é injetado nos adapters de negócio que
    precisam registrar auditoria, encapsulando a criação/persistência do
    AuditLog. A resolução de `actor_role` também é centralizada aqui: o
    papel deve ser o snapshot do momento da ação — nunca um JOIN com a
    tabela users, já que o papel do usuário pode mudar depois e o log
    precisa refletir o papel que ele tinha quando agiu.

    Se o adapter chamador já tiver o User carregado (por precisar dele
    para outra regra de negócio), pode passá-lo via `actor`, evitando uma
    segunda consulta ao repositório. Caso contrário, basta informar
    `actor_id` que o próprio AuditLogger busca o usuário.
    """

    def __init__(
        self,
        audit_log_repository: AuditLogRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self.audit_log_repository = audit_log_repository
        self.user_repository = user_repository

    async def log(
        self,
        action: AuditAction,
        description: str,
        actor_id: Optional[UUID] = None,
        actor: Optional[User] = None,
    ) -> AuditLog:
        if actor is None and actor_id is not None:
            actor = await self.user_repository.get(actor_id)

        actor_role = actor.role.value if actor is not None and actor.role else None

        audit_log = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        return await self.audit_log_repository.save(audit_log)