from typing import Annotated

from fastapi import Depends

from core.business.audit.audit_logger import AuditLogger
from core.persistence.audit.audit_log_repository_port import AuditLogRepositoryPort
from web.dependencies.persistence_dependencies import get_audit_log_repository


def get_audit_logger(
    audit_log_repository: Annotated[
        AuditLogRepositoryPort, Depends(get_audit_log_repository)
    ],
) -> AuditLogger:
    return AuditLogger(audit_log_repository)