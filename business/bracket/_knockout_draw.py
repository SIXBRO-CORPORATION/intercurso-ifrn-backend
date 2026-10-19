import random
from typing import List, Tuple
from uuid import UUID

from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.match.match import Match


def find_first_round_knockout_slots(matches: List[Match]) -> List[Match]:

    targeted_ids = {m.next_match_id for m in matches if m.next_match_id is not None}
    return [
        m
        for m in matches
        if m.match_category == MatchCategory.KNOCKOUT
        and m.match_type != MatchType.THIRD_PLACE
        and m.id not in targeted_ids
    ]


def group_stage_pending_matches(matches: List[Match]) -> List[Match]:
    return [
        m
        for m in matches
        if m.match_category == MatchCategory.GROUP and m.status != MatchStatus.FINISHED
    ]


def knockout_stage_already_drawn(first_round_slots: List[Match]) -> bool:

    return any(
        slot.team1_id is not None or slot.team2_id is not None
        for slot in first_round_slots
    )


def draw_knockout_pairs(
    classified_teams: List[Tuple[UUID, UUID]],
    max_attempts: int = 200,
) -> List[Tuple[UUID, UUID]]:

    for _ in range(max_attempts):
        pairs = _try_draw_pairs(classified_teams)
        if pairs is not None:
            return pairs

    return _draw_pairs_without_constraint(classified_teams)


def _try_draw_pairs(
    classified_teams: List[Tuple[UUID, UUID]],
) -> List[Tuple[UUID, UUID]] | None:
    remaining = list(classified_teams)
    random.shuffle(remaining)

    pairs: List[Tuple[UUID, UUID]] = []
    while remaining:
        team_id, group_id = remaining.pop()
        candidate_indexes = [
            i for i, (_, other_group_id) in enumerate(remaining)
            if other_group_id != group_id
        ]
        if not candidate_indexes:
            return None
        opponent_index = random.choice(candidate_indexes)
        opponent_id, _ = remaining.pop(opponent_index)
        pairs.append((team_id, opponent_id))

    return pairs


def _draw_pairs_without_constraint(
    classified_teams: List[Tuple[UUID, UUID]],
) -> List[Tuple[UUID, UUID]]:
    remaining = [team_id for team_id, _ in classified_teams]
    random.shuffle(remaining)
    return [
        (remaining[i], remaining[i + 1]) for i in range(0, len(remaining), 2)
    ]


def classified_teams_by_group(
    groups_with_standings: List[Tuple[UUID, List[UUID]]],
    classified_per_group: int,
) -> List[Tuple[UUID, UUID]]:

    return [
        (team_id, group_id)
        for group_id, ranked_team_ids in groups_with_standings
        for team_id in ranked_team_ids[:classified_per_group]
    ]
