from core.business.modality.create_modality_port import CreateModalityPort
from core.context import Context
from core.persistence.modality_repository_port import ModalityRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.modality import Modality


class CreateModalityAdapter(CreateModalityPort):
    def __init__(self, modality_repository: ModalityRepositoryPort):
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Modality:
        modality = context.get_data(Modality)

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

        return await self.modality_repository.save(new_modality)
