from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.audit.audit_log_repository_port import AuditLogRepositoryPort
from domain.audit.audit_log import AuditLog
from persistence.mappers.audit.audit_log_mapper import AuditLogMapper
from persistence.model.audit.audit_log_entity import AuditLogEntity


class AuditLogRepositoryAdapter(AuditLogRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: AuditLogMapper):
        self.session = session
        self.mapper = mapper

    async def save(self, audit_log: AuditLog) -> AuditLog:
        entity = self.mapper.to_entity(audit_log)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def find_all(self) -> List[AuditLog]:
        selecionar = select(AuditLogEntity).order_by(
            AuditLogEntity.created_at.desc()
        )
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]

    async def find_by_actor_id(self, actor_id: UUID) -> List[AuditLog]:
        selecionar = (
            select(AuditLogEntity)
            .where(AuditLogEntity.actor_id == actor_id)
            .order_by(AuditLogEntity.created_at.desc())
        )
        result = await self.session.execute(selecionar)
        entities = result.scalars().all()
        return [self.mapper.to_domain(entity) for entity in entities]