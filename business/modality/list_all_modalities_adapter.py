from typing import List

from business.modality.modality_configuration_assembler import attach_configurations
from core.business.modality.list_all_modalities_port import ListAllModalitiesPort
from core.context import Context
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from domain.modality.modality import Modality


class ListAllModalitiesAdapter(ListAllModalitiesPort):

    def __init__(
        self,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
    ):
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository

    async def execute(self, context: Context) -> List[Modality]:
        modalities = await self.modality_repository.find_all()

        configurations = await attach_configurations(
            modalities, self.modality_configuration_repository
        )
        context.put_property("modality_configurations", configurations)

        return modalities
