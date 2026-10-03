from typing import List, Tuple
from uuid import UUID

from business.bracket._read_shared import build_bracket_stats, load_team_names
from core.business.bracket.get_bracket_details_port import GetBracketDetailsPort
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import (
    BracketGroupRepositoryPort,
)
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.exceptions.business_exception import BusinessException


class GetBracketDetailsAdapter(GetBracketDetailsPort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        bracket_group_team_repository: BracketGroupTeamRepositoryPort,
        match_repository: MatchRepositoryPort,
        team_repository: TeamRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.bracket_group_team_repository = bracket_group_team_repository
        self.match_repository = match_repository
        self.team_repository = team_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Bracket:
        bracket_id = context.get_property("bracket_id", UUID)
        if bracket_id is None:
            raise BusinessException("Identificador do chaveamento é obrigatório")

        bracket = await self.bracket_repository.get(bracket_id)
        if bracket is None:
            raise BusinessException("Chaveamento não encontrado")

        matches = await self.match_repository.find_by_bracket(bracket_id)

        groups = await self.bracket_group_repository.find_by_bracket(bracket_id)
        groups_sorted = sorted(groups, key=lambda group: group.display_order or 0)

        groups_with_teams: List[Tuple[BracketGroup, List[BracketGroupTeam]]] = []
        for group in groups_sorted:
            group_teams = await self.bracket_group_team_repository.find_by_group(group.id)
            groups_with_teams.append((group, group_teams))

        team_ids = {match.team1_id for match in matches} | {
            match.team2_id for match in matches
        }
        team_ids |= {
            group_team.team_id
            for _, group_teams in groups_with_teams
            for group_team in group_teams
        }
        team_names = await load_team_names(self.team_repository, team_ids)

        modalities = await self.modality_repository.find_by_ids([bracket.modality_id])
        modality_name = modalities[0].name if modalities else None

        context.put_property("modality_name", modality_name)
        context.put_property("bracket_stats", build_bracket_stats(bracket, matches))
        context.put_property("bracket_groups", groups_with_teams)
        context.put_property("bracket_matches", matches)
        context.put_property("team_names", team_names)

        return bracket
