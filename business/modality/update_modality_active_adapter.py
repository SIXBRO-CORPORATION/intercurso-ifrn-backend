from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.modality.update_modality_active_port import (
    UpdateModalityActivePort,
)
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.exceptions.business_exception import BusinessException
from domain.exceptions.not_found_exception import NotFoundException
from domain.modality.modality import Modality


class UpdateModalityActiveAdapter(UpdateModalityActivePort):
    def __init__(
        self,
        modality_repository: ModalityRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.modality_repository = modality_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Modality:
        modality_id = context.get_property("modality_id", UUID)
        active = context.get_property("active", bool)
        updated_by = context.get_property("updated_by", UUID)

        if modality_id is None:
            raise BusinessException("Identificador da modalidade é obrigatório")

        if active is None:
            raise BusinessException("O campo 'active' é obrigatório")

        modality = await self.modality_repository.get(modality_id)
        if modality is None:
            raise NotFoundException("Modalidade não encontrada")

        if modality.active == active:
            return modality

        modality.active = active

        saved_modality = await self.modality_repository.save(modality)

        await self.audit_logger.log(
            action=(
                AuditAction.MODALITY_ACTIVATED
                if active
                else AuditAction.MODALITY_DEACTIVATED
            ),
            description=(
                f"Modalidade '{saved_modality.name}' "
                f"{'ativada' if active else 'desativada'}"
            ),
            actor_id=updated_by,
        )

        return saved_modality
