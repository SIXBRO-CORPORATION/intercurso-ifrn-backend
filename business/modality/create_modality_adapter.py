from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.modality.create_modality_port import CreateModalityPort
from core.context import Context
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


class CreateModalityAdapter(CreateModalityPort):
    def __init__(
        self,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Modality:
        modality = context.get_data(Modality)
        configuration = context.get_property(
            "modality_configuration", ModalityConfiguration
        )
        created_by = context.get_property("created_by", UUID)

        if modality is None:
            raise BusinessException("Dados da modalidade são obrigatórios")

        if not modality.name or not modality.name.strip():
            raise BusinessException("Nome da modalidade não pode estar vazio")

        if modality.min_members is None or modality.min_members < 1:
            raise BusinessException("Mínimo de membros deve ser maior ou igual a 1")

        if modality.max_members is None or modality.max_members < modality.min_members:
            raise BusinessException(
                "Máximo de membros deve ser maior ou igual ao mínimo de membros"
            )

        if configuration is None:
            raise BusinessException("Configuração de partida é obrigatória")

        if configuration.num_periods is None or configuration.num_periods < 1:
            raise BusinessException("Número de períodos deve ser maior ou igual a 1")

        if (
            configuration.period_durations_minutes is None
            or configuration.period_durations_minutes < 1
        ):
            raise BusinessException(
                "Duração do período deve ser maior ou igual a 1 minuto"
            )

        if configuration.score_type is None:
            raise BusinessException("Sistema de pontuação é obrigatório")

        normalized_name = modality.name.strip()

        existing_modality = await self.modality_repository.find_by_name(
            normalized_name
        )
        if existing_modality is not None:
            raise BusinessException(
                "Já existe uma modalidade cadastrada com esse nome"
            )

        new_modality = Modality(
            name=normalized_name,
            min_members=modality.min_members,
            max_members=modality.max_members,
            active=True,
        )

        saved_modality = await self.modality_repository.save(new_modality)

        new_configuration = ModalityConfiguration(
            modality_id=saved_modality.id,
            num_periods=configuration.num_periods,
            period_durations_minutes=configuration.period_durations_minutes,
            score_type=configuration.score_type,
            has_third_place_match=bool(configuration.has_third_place_match),
            metadata=configuration.metadata,
            active=True,
        )
        saved_configuration = await self.modality_configuration_repository.save(
            new_configuration
        )
        context.put_property("modality_configuration", saved_configuration)

        created_by_user = (
            await self.user_repository.get(created_by) if created_by else None
        )
        actor_role = (
            created_by_user.role.value
            if created_by_user is not None and created_by_user.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.MODALITY_CREATED,
            description=f"Modalidade '{saved_modality.name}' cadastrada",
            actor_id=created_by,
            actor_role=actor_role,
        )

        return saved_modality