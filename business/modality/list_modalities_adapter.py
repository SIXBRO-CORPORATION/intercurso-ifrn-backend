from typing import List, Optional
from uuid import UUID

from business.modality.modality_configuration_assembler import attach_configurations
from core.business.modality.list_modalities_port import ListModalitiesPort
from core.context import Context
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.modality.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from domain.modality.modality import Modality


class ListModalitiesAdapter(ListModalitiesPort):

    def __init__(
        self,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
        volleyball_modality_configuration_repository: Optional[
            VolleyballModalityConfigurationRepositoryPort
        ] = None,
    ):
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository
        self.volleyball_modality_configuration_repository = (
            volleyball_modality_configuration_repository
        )

    async def execute(self, context: Context) -> List[Modality]:
        season_id = context.get_property("season_id", UUID)
        if season_id is None:
            modalities = await self.modality_repository.find_active_modalities()
        else:
            modalities = await self.modality_repository.find_active_by_season(
                season_id
            )

        configurations, volleyball_configurations = await attach_configurations(
            modalities,
            self.modality_configuration_repository,
            self.volleyball_modality_configuration_repository,
        )
        context.put_property("modality_configurations", configurations)
        context.put_property(
            "modality_volleyball_configurations", volleyball_configurations
        )

        return modalities
