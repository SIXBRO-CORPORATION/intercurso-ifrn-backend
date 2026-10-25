from math import comb

from business.bracket.engine.draw_engine import next_power_of_two
from domain.enums.modality_format import ModalityFormat


def _knockout_rounds(bracket_size: int) -> list[int]:

    rounds: list[int] = []
    size = bracket_size
    while size > 1:
        matches_in_round = size // 2
        rounds.append(matches_in_round)
        size = matches_in_round
    return rounds


def estimate_match_counts(
    modality_format: ModalityFormat, team_count: int, configuration: dict
) -> dict:

    if modality_format == ModalityFormat.KNOCKOUT:
        rounds = _knockout_rounds(next_power_of_two(team_count))
        return {"total_matches": sum(rounds), "matches_by_round": rounds}

    if modality_format == ModalityFormat.GROUP_STAGE_KNOCKOUT:
        group_sizes = configuration.get("group_sizes") or []
        group_stage_matches = sum(comb(size, 2) for size in group_sizes)

        num_groups = configuration.get("num_groups") or 0
        classified_per_group = configuration.get("classified_per_group") or 0
        knockout_rounds = _knockout_rounds(num_groups * classified_per_group)

        matches_by_round = [group_stage_matches, *knockout_rounds]
        return {"total_matches": sum(matches_by_round), "matches_by_round": matches_by_round}

    if modality_format == ModalityFormat.ROUND_ROBIN:
        rounds = configuration.get("rounds") or 1
        matches_per_turn = comb(team_count, 2)
        matches_by_round = [matches_per_turn] * rounds
        return {"total_matches": sum(matches_by_round), "matches_by_round": matches_by_round}

    if modality_format == ModalityFormat.TRIANGULAR:
        turns = 2 if configuration.get("double_round") else 1
        matches_by_round = [comb(team_count, 2)] * turns
        return {"total_matches": sum(matches_by_round), "matches_by_round": matches_by_round}

    return {"total_matches": 0, "matches_by_round": []}
