from typing import Dict, List, Optional, Tuple
from uuid import UUID

from domain.enums.match_category import MatchCategory
from domain.enums.match_type import MatchType
from domain.match.match import Match

_NAMED_ROUNDS_BY_DEPTH = {
    0: "Final",
    1: "Semifinal",
    2: "Quartas de final",
    3: "Oitavas de final",
}


def _depth_from_final(
    match: Match,
    matches_by_id: Dict[UUID, Match],
    cache: Dict[UUID, int],
    visiting: set,
) -> int:
    if match.id in cache:
        return cache[match.id]

    if match.next_match_id is None or match.id in visiting:
        cache[match.id] = 0
        return 0

    next_match = matches_by_id.get(match.next_match_id)
    if next_match is None:
        cache[match.id] = 0
        return 0

    visiting.add(match.id)
    depth = 1 + _depth_from_final(next_match, matches_by_id, cache, visiting)
    visiting.discard(match.id)

    cache[match.id] = depth
    return depth


def build_round_info(
    matches: List[Match],
) -> Dict[UUID, Tuple[Optional[str], Optional[int]]]:

    knockout_matches = [
        m
        for m in matches
        if m.match_category == MatchCategory.KNOCKOUT
        and m.match_type != MatchType.THIRD_PLACE
    ]
    if not knockout_matches:
        return {}

    matches_by_id = {m.id: m for m in knockout_matches}
    cache: Dict[UUID, int] = {}
    depths = {
        match.id: _depth_from_final(match, matches_by_id, cache, set())
        for match in knockout_matches
    }

    max_depth = max(depths.values())

    info: Dict[UUID, Tuple[Optional[str], Optional[int]]] = {}
    for match in knockout_matches:
        depth = depths[match.id]
        round_order = max_depth - depth + 1
        if depth in _NAMED_ROUNDS_BY_DEPTH:
            round_name = _NAMED_ROUNDS_BY_DEPTH[depth]
        else:
            teams_in_round = 2 ** (depth + 1)
            round_name = f"Rodada de {teams_in_round} times"
        info[match.id] = (round_name, round_order)

    final_round_order = max_depth + 1
    for match in matches:
        if match.match_type == MatchType.THIRD_PLACE:
            info[match.id] = ("Disputa de 3º lugar", final_round_order)

    return info
