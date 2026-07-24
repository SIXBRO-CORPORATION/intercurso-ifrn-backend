from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.enums.audit_action import AuditAction


@dataclass
class AuditLog:
    """Registro imutável de auditoria.

    Diferente das demais entidades do domínio, AuditLog não herda de
    AbstractDomain: um log de auditoria não possui modified_at, deleted_at
    ou active — não faz sentido "inativar" ou "editar" um registro de
    auditoria já criado.
    """

    id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    action: Optional[AuditAction] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None