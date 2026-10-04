from datetime import datetime
from typing import List
from uuid import UUID

from core.business.match.list_public_matches_port import ListPublicMatchesPort
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import (
    BracketGroupRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


class ListPublicMatchesAdapter(ListPublicMatchesPort):
    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        team_repository: TeamRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.match_repository = match_repository
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.team_repository = team_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> List[Match]:
        season_id = context.get_property("season_id", UUID)
        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")
        date_from = context.get_property("date_from", datetime)
        date_to = context.get_property("date_to", datetime)
        if date_from and date_to and date_from > date_to:
            raise BusinessException("date_from não pode ser posterior a date_to")
        page = context.get_property("page", int) or 1
        size = context.get_property("size", int) or 20

        matches, total = await self.match_repository.search_by_season(
            season_id,
            context.get_property("modality_id", UUID),
            context.get_property("status", MatchStatus),
            date_from,
            date_to,
            (page - 1) * size,
            size,
        )

        brackets = await self.bracket_repository.find_by_ids(
            list({m.bracket_id for m in matches})
        )
        modalities = {
            m.id: m
            for m in await self.modality_repository.find_by_ids(
                list({b.modality_id for b in brackets})
            )
        }
        groups = await self.bracket_group_repository.find_by_ids(
            list({m.bracket_group_id for m in matches if m.bracket_group_id})
        )
        teams = await self.team_repository.find_by_ids(
            list({t for m in matches for t in (m.team1_id, m.team2_id) if t})
        )

        for match in matches:
            match.sync_clock()

        context.put_property("total", total)
        context.put_property("page", page)
        context.put_property("size", size)
        context.put_property("teams", {t.id: t for t in teams})
        context.put_property("group_names", {g.id: g.name for g in groups})
        context.put_property(
            "bracket_modalities",
            {b.id: modalities[b.modality_id] for b in brackets if b.modality_id in modalities},
        )
        return matches
