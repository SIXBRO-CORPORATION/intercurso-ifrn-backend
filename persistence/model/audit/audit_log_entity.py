import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UUID

from persistence.model.abstract_entity import Base


class AuditLogEntity(Base):
    """Tabela de auditoria.

    Não herda de AbstractEntity de propósito: log é imutável (sem
    modified_at/deleted_at/active) e o __tablename__ precisa ser "logs"
    (o auto-gerado a partir de "AuditLog" seria "audit_logs").
    """

    __tablename__ = "logs"

    id = Column(UUID, primary_key=True, default=lambda: uuid.uuid4())

    actor_id = Column(ForeignKey("users.id"), nullable=True, index=True)

    actor_role = Column(String(20), nullable=True)

    action = Column(String(50), nullable=False, index=True)

    description = Column(String(500), nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(),
        index=True,
    )