from typing import List
from uuid import UUID

from business.bracket._read_shared import build_bracket_stats
from core.business.bracket.list_brackets_by_season_port import ListBracketsBySeasonPort
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from domain.bracket.bracket import Bracket
from domain.exceptions.business_exception import BusinessException


class ListBracketsBySeasonAdapter(ListBracketsBySeasonPort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        match_repository: MatchRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.bracket_repository = bracket_repository
        self.match_repository = match_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> List[Bracket]:
        season_id = context.get_property("season_id", UUID)
        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        brackets = await self.bracket_repository.find_by_season(season_id)

        stats = {}
        # ponytail: one find_by_bracket per bracket (N+1); fine while a season has few modalities
        for bracket in brackets:
            matches = await self.match_repository.find_by_bracket(bracket.id)
            stats[bracket.id] = build_bracket_stats(bracket, matches)

        modality_names = {}
        modality_ids = list({bracket.modality_id for bracket in brackets})
        if modality_ids:
            modalities = await self.modality_repository.find_by_ids(modality_ids)
            modality_names = {modality.id: modality.name for modality in modalities}

        context.put_property("bracket_stats", stats)
        context.put_property("modality_names", modality_names)

        return brackets
