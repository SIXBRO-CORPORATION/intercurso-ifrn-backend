from typing import Callable, Dict, List
from uuid import UUID

from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.match.match import Match


def _average(for_: int, against: int) -> float:

    if against == 0:
        return float("inf") if for_ > 0 else 0.0
    return for_ / against


def _head_to_head_table(
    team_ids: List[UUID], matches: List[Match]
) -> Dict[UUID, Dict[str, int]]:

    stats = {tid: {"points": 0, "wins": 0, "gf": 0, "ga": 0} for tid in team_ids}
    id_set = set(team_ids)
    for match in matches:
        if match.team1_id not in id_set or match.team2_id not in id_set:
            continue

        score1, score2 = match.team1_score or 0, match.team2_score or 0
        stats[match.team1_id]["gf"] += score1
        stats[match.team1_id]["ga"] += score2
        stats[match.team2_id]["gf"] += score2
        stats[match.team2_id]["ga"] += score1

        if match.winner_id == match.team1_id:
            stats[match.team1_id]["wins"] += 1
            stats[match.team1_id]["points"] += 3
        elif match.winner_id == match.team2_id:
            stats[match.team2_id]["wins"] += 1
            stats[match.team2_id]["points"] += 3
        else:
            stats[match.team1_id]["points"] += 1
            stats[match.team2_id]["points"] += 1

    return stats


def _bucket_by(
    cluster: List[UUID], key_fn: Callable[[UUID], float]
) -> List[List[UUID]]:

    grouped: Dict[float, List[UUID]] = {}
    for tid in cluster:
        grouped.setdefault(key_fn(tid), []).append(tid)
    return [grouped[key] for key in sorted(grouped.keys(), reverse=True)]


def order_group_standings(
    group_teams: List[BracketGroupTeam], matches: List[Match]
) -> List[BracketGroupTeam]:

    finished_group_matches = [
        m
        for m in matches
        if m.status == MatchStatus.FINISHED
        and m.match_category == MatchCategory.GROUP
    ]

    teams_by_id = {t.team_id: t for t in group_teams}

    def resolve(cluster: List[UUID], criteria_used: int) -> List[UUID]:
        if len(cluster) <= 1:
            return cluster

        if criteria_used == 0:  # I - confronto direto
            mini = _head_to_head_table(cluster, finished_group_matches)
            buckets = _bucket_by(cluster, lambda tid: mini[tid]["points"])
        elif criteria_used == 1:  # II - maior número de vitórias
            buckets = _bucket_by(cluster, lambda tid: teams_by_id[tid].wins or 0)
        elif criteria_used == 2:  # III - saldo entre as equipes empatadas
            mini = _head_to_head_table(cluster, finished_group_matches)
            buckets = _bucket_by(
                cluster, lambda tid: mini[tid]["gf"] - mini[tid]["ga"]
            )
        elif criteria_used == 3:  # IV - average entre as equipes empatadas
            mini = _head_to_head_table(cluster, finished_group_matches)
            buckets = _bucket_by(
                cluster, lambda tid: _average(mini[tid]["gf"], mini[tid]["ga"])
            )
        elif criteria_used == 4:  # V - menor número de gols sofridos (geral)
            buckets = _bucket_by(
                cluster, lambda tid: -(teams_by_id[tid].goals_against or 0)
            )
        elif criteria_used == 5:  # VI - saldo geral do grupo
            buckets = _bucket_by(
                cluster, lambda tid: teams_by_id[tid].goals_difference or 0
            )
        elif criteria_used == 6:  # VII - average geral do grupo
            buckets = _bucket_by(
                cluster,
                lambda tid: _average(
                    teams_by_id[tid].goals_for or 0,
                    teams_by_id[tid].goals_against or 0,
                ),
            )
        else:  # VIII - sorteio (fora do alcance do sistema)
            return sorted(cluster, key=str)

        resolved: List[UUID] = []
        for bucket in buckets:
            resolved.extend(resolve(bucket, criteria_used + 1))
        return resolved

    points_buckets = _bucket_by(
        list(teams_by_id.keys()), lambda tid: teams_by_id[tid].points or 0
    )

    ordered_ids: List[UUID] = []
    for bucket in points_buckets:
        ordered_ids.extend(resolve(bucket, criteria_used=0))

    return [teams_by_id[tid] for tid in ordered_ids]
