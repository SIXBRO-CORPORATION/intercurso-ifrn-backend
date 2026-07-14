import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat


@dataclass
class MatchSpec:
    team1_id: Optional[UUID]
    team2_id: Optional[UUID]
    match_type: MatchType
    match_category: MatchCategory
    status: MatchStatus
    is_bye: bool = False
    winner_id: Optional[UUID] = None
    finished_at: Optional[datetime] = None
    group_index: Optional[int] = None  # índice do grupo em DrawPlan.groups, se houver


@dataclass
class GroupSpec:
    name: str
    display_order: int
    team_ids: List[UUID] = field(default_factory=list)


@dataclass
class DrawPlan:
    groups: List[GroupSpec]
    matches: List[MatchSpec]
    byes_created: int


def next_power_of_two(n: int) -> int:
    power = 1
    while power < n:
        power *= 2
    return power


def _build_first_round_pairs(
    shuffled_teams: List[UUID],
) -> Tuple[List[Tuple[Optional[UUID], Optional[UUID]]], int]:
    """Monta os confrontos da primeira rodada de um mata-mata, distribuindo BYEs
    (quando o total não é potência de 2) de forma que nenhum confronto fique
    BYE-contra-BYE."""
    team_count = len(shuffled_teams)
    size = next_power_of_two(team_count)
    byes_needed = size - team_count
    num_matches = size // 2

    bye_slots = (
        set(random.sample(range(num_matches), byes_needed)) if byes_needed > 0 else set()
    )

    pool = list(shuffled_teams)
    pairs: List[Tuple[Optional[UUID], Optional[UUID]]] = []
    for i in range(num_matches):
        if i in bye_slots:
            pairs.append((pool.pop(), None))
        else:
            t1 = pool.pop()
            t2 = pool.pop()
            pairs.append((t1, t2))

    return pairs, byes_needed


def build_knockout_tree(
    first_round_pairs: List[Tuple[Optional[UUID], Optional[UUID]]],
    has_third_place: bool,
    group_index: Optional[int] = None,
) -> List[MatchSpec]:
    """Constrói toda a árvore de mata-mata a partir dos confrontos da primeira
    rodada (que podem já vir totalmente definidos, parcialmente TBD por conta de
    BYE, ou totalmente TBD no caso da fase de mata-mata pós-grupos)."""
    now = datetime.now()

    rounds: List[List[MatchSpec]] = []
    winners: List[Optional[UUID]] = []
    round_matches: List[MatchSpec] = []

    for team1_id, team2_id in first_round_pairs:
        if team1_id is not None and team2_id is None:
            spec = MatchSpec(
                team1_id=team1_id,
                team2_id=None,
                match_type=MatchType.REGULAR,
                match_category=MatchCategory.KNOCKOUT,
                status=MatchStatus.FINISHED,
                is_bye=True,
                winner_id=team1_id,
                finished_at=now,
                group_index=group_index,
            )
            winners.append(team1_id)
        else:
            spec = MatchSpec(
                team1_id=team1_id,
                team2_id=team2_id,
                match_type=MatchType.REGULAR,
                match_category=MatchCategory.KNOCKOUT,
                status=MatchStatus.SCHEDULED,
                group_index=group_index,
            )
            winners.append(None)
        round_matches.append(spec)

    rounds.append(round_matches)

    while len(round_matches) > 1:
        next_round: List[MatchSpec] = []
        next_winners: List[Optional[UUID]] = []
        for i in range(0, len(round_matches), 2):
            w1 = winners[i]
            w2 = winners[i + 1]
            next_round.append(
                MatchSpec(
                    team1_id=w1,
                    team2_id=w2,
                    match_type=MatchType.REGULAR,
                    match_category=MatchCategory.KNOCKOUT,
                    status=MatchStatus.SCHEDULED,
                    group_index=group_index,
                )
            )
            next_winners.append(None)
        round_matches = next_round
        winners = next_winners
        rounds.append(round_matches)

    total_rounds = len(rounds)
    for round_index, matches_in_round in enumerate(rounds):
        if round_index == total_rounds - 1:
            match_type = MatchType.FINAL
        elif round_index == total_rounds - 2:
            match_type = MatchType.SEMIFINAL
        else:
            match_type = MatchType.REGULAR
        for match_spec in matches_in_round:
            match_spec.match_type = match_type

    all_matches: List[MatchSpec] = [m for round_matches in rounds for m in round_matches]

    if has_third_place and total_rounds >= 2:
        all_matches.append(
            MatchSpec(
                team1_id=None,
                team2_id=None,
                match_type=MatchType.THIRD_PLACE,
                match_category=MatchCategory.KNOCKOUT,
                status=MatchStatus.SCHEDULED,
                group_index=group_index,
            )
        )

    return all_matches


def _round_robin_pairs(
    team_ids: List[UUID], rounds: int
) -> List[Tuple[UUID, UUID]]:
    """Método do círculo clássico para gerar confrontos de todos-contra-todos,
    lidando com número ímpar de times (um time 'descansa' por rodada, sem gerar
    partida nem BYE)."""
    teams: List[Optional[UUID]] = list(team_ids)
    if len(teams) % 2 == 1:
        teams.append(None)

    n = len(teams)
    half = n // 2
    arr = teams[:]
    schedule: List[Tuple[UUID, UUID]] = []

    for _ in range(n - 1):
        for i in range(half):
            t1 = arr[i]
            t2 = arr[n - 1 - i]
            if t1 is not None and t2 is not None:
                schedule.append((t1, t2))
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]

    if rounds == 2:
        schedule = schedule + [(t2, t1) for (t1, t2) in schedule]

    return schedule


def _build_round_robin_matches(
    team_ids: List[UUID], rounds: int, group_index: Optional[int]
) -> List[MatchSpec]:
    pairs = _round_robin_pairs(team_ids, rounds)
    return [
        MatchSpec(
            team1_id=t1,
            team2_id=t2,
            match_type=MatchType.REGULAR,
            match_category=MatchCategory.GROUP,
            status=MatchStatus.SCHEDULED,
            group_index=group_index,
        )
        for (t1, t2) in pairs
    ]


def build_draw(
    modality_format: ModalityFormat,
    team_ids: List[UUID],
    configuration: dict,
) -> DrawPlan:
    """Função pura (sem I/O) que monta o plano completo de sorteio: grupos (se
    houver) e todas as partidas de todas as fases, já com BYE resolvido e
    TBD marcado onde aplicável. Não persiste nada — quem chama decide o que
    fazer com o resultado."""
    shuffled = list(team_ids)
    random.shuffle(shuffled)

    if modality_format == ModalityFormat.KNOCKOUT:
        first_round_pairs, byes_created = _build_first_round_pairs(shuffled)
        matches = build_knockout_tree(first_round_pairs, has_third_place=True)
        return DrawPlan(groups=[], matches=matches, byes_created=byes_created)

    if modality_format == ModalityFormat.ROUND_ROBIN:
        group = GroupSpec(name="Geral", display_order=0, team_ids=shuffled)
        matches = _build_round_robin_matches(
            shuffled, configuration.get("rounds", 1), group_index=0
        )
        return DrawPlan(groups=[group], matches=matches, byes_created=0)

    if modality_format == ModalityFormat.TRIANGULAR:
        group = GroupSpec(name="Geral", display_order=0, team_ids=shuffled)
        rounds = 2 if configuration.get("double_round") else 1
        matches = _build_round_robin_matches(shuffled, rounds, group_index=0)
        return DrawPlan(groups=[group], matches=matches, byes_created=0)

    if modality_format == ModalityFormat.GROUP_STAGE_KNOCKOUT:
        group_sizes: List[int] = configuration["group_sizes"]
        classified_per_group: int = configuration["classified_per_group"]

        groups: List[GroupSpec] = []
        group_matches: List[MatchSpec] = []
        pool = list(shuffled)
        for index, size in enumerate(group_sizes):
            group_team_ids = [pool.pop() for _ in range(size)]
            group_name = f"Grupo {chr(ord('A') + index)}"
            groups.append(
                GroupSpec(name=group_name, display_order=index, team_ids=group_team_ids)
            )
            group_matches.extend(
                _build_round_robin_matches(group_team_ids, rounds=1, group_index=index)
            )

        total_classified = len(group_sizes) * classified_per_group
        knockout_first_round_pairs: List[Tuple[Optional[UUID], Optional[UUID]]] = [
            (None, None) for _ in range(total_classified // 2)
        ]
        knockout_matches = build_knockout_tree(
            knockout_first_round_pairs, has_third_place=True, group_index=None
        )

        return DrawPlan(
            groups=groups, matches=group_matches + knockout_matches, byes_created=0
        )

    raise ValueError(f"Formato de chaveamento não suportado: {modality_format}")
