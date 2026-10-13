from uuid import uuid4

from business.bracket._knockout_draw import (
    classified_teams_by_group,
    draw_knockout_pairs,
    find_first_round_knockout_slots,
    group_stage_pending_matches,
    knockout_stage_already_drawn,
)
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.match.match import Match


def make_match(
    match_category,
    match_type=MatchType.REGULAR,
    status=MatchStatus.SCHEDULED,
    team1_id=None,
    team2_id=None,
    next_match_id=None,
    match_id=None,
):
    return Match(
        id=match_id or uuid4(),
        team1_id=team1_id,
        team2_id=team2_id,
        match_category=match_category,
        match_type=match_type,
        status=status,
        next_match_id=next_match_id,
    )


def build_group_stage_knockout_bracket(num_groups=4, classified_per_group=2):
    """Monta um esqueleto de chaveamento GROUP_STAGE_KNOCKOUT já persistido:
    N grupos (times já definidos, partidas finalizadas) + árvore de
    mata-mata com times TBD, exatamente como `persist_draw_matches` deixaria
    antes do sorteio do mata-mata."""
    group_matches = [
        make_match(
            MatchCategory.GROUP,
            status=MatchStatus.FINISHED,
            team1_id=uuid4(),
            team2_id=uuid4(),
        )
        for _ in range(num_groups * 3)
    ]

    total_classified = num_groups * classified_per_group

    if total_classified == 2:
        # Só 1 confronto no total -> ele já nasce como FINAL, sem
        # semifinais nem disputa de 3º lugar (espelha build_knockout_tree).
        final = make_match(MatchCategory.KNOCKOUT, match_type=MatchType.FINAL)
        return group_matches + [final]

    quarters = [
        make_match(MatchCategory.KNOCKOUT, match_type=MatchType.REGULAR)
        for _ in range(total_classified // 2)
    ]
    semis = [
        make_match(MatchCategory.KNOCKOUT, match_type=MatchType.SEMIFINAL)
        for _ in range(len(quarters) // 2)
    ]
    for i, q in enumerate(quarters):
        q.next_match_id = semis[i // 2].id

    final = make_match(MatchCategory.KNOCKOUT, match_type=MatchType.FINAL)
    for i, s in enumerate(semis):
        s.next_match_id = final.id

    third_place = make_match(MatchCategory.KNOCKOUT, match_type=MatchType.THIRD_PLACE)

    return group_matches + quarters + semis + [final, third_place]


class TestFindFirstRoundKnockoutSlots:
    def test_returns_only_untargeted_regular_knockout_matches(self):
        matches = build_group_stage_knockout_bracket(num_groups=4, classified_per_group=2)

        slots = find_first_round_knockout_slots(matches)

        # 4 grupos x 2 classificados = 8 -> 4 confrontos de quartas
        assert len(slots) == 4
        assert all(m.match_type == MatchType.REGULAR for m in slots)

    def test_excludes_third_place_match(self):
        matches = build_group_stage_knockout_bracket()
        slots = find_first_round_knockout_slots(matches)
        assert all(m.match_type != MatchType.THIRD_PLACE for m in slots)

    def test_excludes_semifinal_and_final(self):
        matches = build_group_stage_knockout_bracket()
        slots = find_first_round_knockout_slots(matches)
        assert all(
            m.match_type not in (MatchType.SEMIFINAL, MatchType.FINAL) for m in slots
        )

    def test_two_classified_total_treats_the_single_final_as_first_round(self):
        """Caso degenerado: só 2 classificados no total -> só existe 1
        partida de mata-mata, que já nasce como FINAL (sem rodadas antes).
        Ela também deve ser reconhecida como vaga de 1ª rodada."""
        matches = build_group_stage_knockout_bracket(num_groups=2, classified_per_group=1)
        slots = find_first_round_knockout_slots(matches)
        assert len(slots) == 1
        assert slots[0].match_type == MatchType.FINAL


class TestGroupStagePendingMatches:
    def test_empty_when_all_group_matches_finished(self):
        matches = build_group_stage_knockout_bracket()
        assert group_stage_pending_matches(matches) == []

    def test_lists_unfinished_group_matches_only(self):
        matches = build_group_stage_knockout_bracket()
        matches[0].status = MatchStatus.IN_PROGRESS

        pending = group_stage_pending_matches(matches)

        assert len(pending) == 1
        assert pending[0].match_category == MatchCategory.GROUP


class TestKnockoutStageAlreadyDrawn:
    def test_false_when_all_slots_tbd(self):
        matches = build_group_stage_knockout_bracket()
        slots = find_first_round_knockout_slots(matches)
        assert knockout_stage_already_drawn(slots) is False

    def test_true_when_any_slot_has_a_team(self):
        matches = build_group_stage_knockout_bracket()
        slots = find_first_round_knockout_slots(matches)
        slots[0].team1_id = uuid4()
        assert knockout_stage_already_drawn(slots) is True


class TestClassifiedTeamsByGroup:
    def test_takes_only_top_n_per_group_preserving_group_id(self):
        group_a, group_b = uuid4(), uuid4()
        a1, a2, a3 = uuid4(), uuid4(), uuid4()
        b1, b2 = uuid4(), uuid4()
        groups_with_standings = [(group_a, [a1, a2, a3]), (group_b, [b1, b2])]

        result = classified_teams_by_group(groups_with_standings, classified_per_group=2)

        assert set(result) == {(a1, group_a), (a2, group_a), (b1, group_b), (b2, group_b)}


class TestDrawKnockoutPairs:
    def test_pairs_every_classified_team_exactly_once(self):
        groups = [uuid4() for _ in range(4)]
        classified = [(uuid4(), g) for g in groups for _ in range(2)]

        pairs = draw_knockout_pairs(classified)

        paired_teams = [team for pair in pairs for team in pair]
        assert sorted(paired_teams) == sorted(team_id for team_id, _ in classified)
        assert len(pairs) == len(classified) // 2

    def test_never_pairs_two_teams_from_the_same_group_when_avoidable(self):
        group_to_teams = {g: [uuid4(), uuid4()] for g in [uuid4() for _ in range(4)]}
        classified = [
            (team_id, group_id)
            for group_id, team_ids in group_to_teams.items()
            for team_id in team_ids
        ]
        team_to_group = dict(classified)

        for _ in range(20):  # roda várias vezes por causa da aleatoriedade
            pairs = draw_knockout_pairs(classified)
            for t1, t2 in pairs:
                assert team_to_group[t1] != team_to_group[t2]

    def test_falls_back_to_unconstrained_pairing_for_a_single_group(self):
        """Grupo único: impossível evitar mesmo-grupo (são todos do mesmo
        grupo) -> não deve travar, só parear mesmo assim."""
        group = uuid4()
        classified = [(uuid4(), group) for _ in range(4)]

        pairs = draw_knockout_pairs(classified)

        assert len(pairs) == 2
        paired_teams = [team for pair in pairs for team in pair]
        assert sorted(paired_teams) == sorted(team_id for team_id, _ in classified)
