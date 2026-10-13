from typing import Dict, Iterable, List, Optional
from uuid import UUID

from business.bracket._knockout_draw import (
    find_first_round_knockout_slots,
    group_stage_pending_matches,
    knockout_stage_already_drawn,
)
from core.persistence.team.team_repository_port import TeamRepositoryPort
from domain.bracket.bracket import Bracket
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.enums.modality_format import ModalityFormat
from domain.match.match import Match

_STARTED_STATUSES = {MatchStatus.IN_PROGRESS, MatchStatus.FINISHED}


def _can_draw_knockout_stage(bracket: Bracket, matches: List[Match]) -> bool:
    if bracket.format != ModalityFormat.GROUP_STAGE_KNOCKOUT:
        return False
    if group_stage_pending_matches(matches):
        return False
    first_round_slots = find_first_round_knockout_slots(matches)
    if not first_round_slots:
        return False
    return not knockout_stage_already_drawn(first_round_slots)


def build_bracket_stats(bracket: Bracket, matches: List[Match]) -> dict:

    started = sum(1 for match in matches if match.status in _STARTED_STATUSES)
    finished = sum(1 for match in matches if match.status == MatchStatus.FINISHED)

    available_actions: List[str] = []
    if bracket.status != BracketStatus.FINISHED and started == 0:
        available_actions.append("resort")
    if bracket.status != BracketStatus.FINISHED and _can_draw_knockout_stage(
        bracket, matches
    ):
        available_actions.append("draw_knockout")

    return {
        "total_matches": len(matches),
        "started_matches": started,
        "finished_matches": finished,
        "available_actions": available_actions,
    }


async def load_team_names(
    team_repository: TeamRepositoryPort, team_ids: Iterable[Optional[UUID]]
) -> Dict[UUID, str]:
    ids = list({tid for tid in team_ids if tid is not None})
    if not ids:
        return {}
    teams = await team_repository.find_by_ids(ids)
    return {team.id: team.name for team in teams}
