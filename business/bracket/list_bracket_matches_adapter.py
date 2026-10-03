from typing import List
from uuid import UUID

from business.bracket._read_shared import load_team_names
from core.business.bracket.list_bracket_matches_port import ListBracketMatchesPort
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import (
    BracketGroupRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


class ListBracketMatchesAdapter(ListBracketMatchesPort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        match_repository: MatchRepositoryPort,
        team_repository: TeamRepositoryPort,
    ):
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.match_repository = match_repository
        self.team_repository = team_repository

    async def execute(self, context: Context) -> List[Match]:
        bracket_id = context.get_property("bracket_id", UUID)
        if bracket_id is None:
            raise BusinessException("Identificador do chaveamento é obrigatório")

        bracket = await self.bracket_repository.get(bracket_id)
        if bracket is None:
            raise BusinessException("Chaveamento não encontrado")

        matches = await self.match_repository.find_by_bracket(bracket_id)
        groups = await self.bracket_group_repository.find_by_bracket(bracket_id)

        team_ids = {match.team1_id for match in matches} | {
            match.team2_id for match in matches
        }
        team_names = await load_team_names(self.team_repository, team_ids)
        group_names = {group.id: group.name for group in groups}

        context.put_property("team_names", team_names)
        context.put_property("group_names", group_names)

        return matches
