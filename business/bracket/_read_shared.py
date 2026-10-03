from typing import Dict, Iterable, List, Optional
from uuid import UUID

from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.match.match import Match

_STARTED_STATUSES = {MatchStatus.IN_PROGRESS, MatchStatus.FINISHED}


def build_bracket_stats(bracket: Bracket, matches: List[Match]) -> dict:

    started = sum(1 for match in matches if match.status in _STARTED_STATUSES)
    finished = sum(1 for match in matches if match.status == MatchStatus.FINISHED)

    available_actions: List[str] = []
    if bracket.status != BracketStatus.FINISHED and started == 0:
        available_actions.append("resort")

    return {
        "total_matches": len(matches),
        "started_matches": started,
        "finished_matches": finished,
        "available_actions": available_actions,
    }


async def load_team_names(
    team_repository: TeamRepositoryPort, team_ids: Iterable[Optional[UUID]]
) -> Dict[UUID, str]:
    # ponytail: one get per team (N+1); add TeamRepositoryPort.find_by_ids when brackets grow past ~32 teams
    names: Dict[UUID, str] = {}
    for team_id in {tid for tid in team_ids if tid is not None}:
        team = await team_repository.get(team_id)
        if team is not None:
            names[team_id] = team.name
    return names
