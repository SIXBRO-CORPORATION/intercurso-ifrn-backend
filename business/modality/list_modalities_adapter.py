from typing import List
from uuid import UUID

from core.business.modality.list_modalities_port import ListModalitiesPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from domain.modality.modality import Modality


class ListModalitiesAdapter(ListModalitiesPort):
    def __init__(self, modality_repository: ModalityRepositoryPort):
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> List[Modality]:
        season_id = context.get_property("season_id", UUID)
        if season_id is None:
            return await self.modality_repository.find_active_modalities()
        return await self.modality_repository.find_active_by_season(season_id)
