from core.business.modality.create_modality_port import CreateModalityPort
from core.context import Context
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration


class CreateModalityAdapter(CreateModalityPort):
    def __init__(
        self,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
    ):
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository

    async def execute(self, context: Context) -> Modality:
        modality = context.get_data(Modality)
        configuration = context.get_property(
            "modality_configuration", ModalityConfiguration
        )

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

        # UC004 - Regras de Negócio 11-15: a configuração de partida é
        # obrigatória e criada junto com a modalidade, na mesma operação.
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

        # TODO (débito técnico assumido nesta fase): registrar a operação em
        # auditoria (monitor responsável, data/hora e ação), conforme exigido
        # pelo UC004. Não há infraestrutura de auditoria no projeto ainda.

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

        return saved_modality
