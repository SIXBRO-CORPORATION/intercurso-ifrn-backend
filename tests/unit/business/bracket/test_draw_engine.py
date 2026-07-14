from uuid import uuid4

import pytest

from business.bracket.engine.config_suggester import (
    resolve_configuration,
    suggest_configuration,
    validate_team_count_for_format,
)
from business.bracket.engine.draw_engine import build_draw, next_power_of_two
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException


def make_team_ids(n):
    return [uuid4() for _ in range(n)]


class TestNextPowerOfTwo:
    @pytest.mark.parametrize(
        "n,expected",
        [(1, 1), (2, 2), (3, 4), (4, 4), (5, 8), (6, 8), (7, 8), (8, 8), (9, 16)],
    )
    def test_next_power_of_two(self, n, expected):
        assert next_power_of_two(n) == expected


class TestKnockoutDraw:
    def test_power_of_two_no_byes(self):
        teams = make_team_ids(8)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})

        assert plan.byes_created == 0
        assert plan.groups == []

        bye_matches = [m for m in plan.matches if m.is_bye]
        assert bye_matches == []

        # 8 times -> 4 (oitavas) + 2 (semis) + 1 (final) + 1 (3º lugar) = 8
        assert len(plan.matches) == 8

        finals = [m for m in plan.matches if m.match_type == MatchType.FINAL]
        semis = [m for m in plan.matches if m.match_type == MatchType.SEMIFINAL]
        thirds = [m for m in plan.matches if m.match_type == MatchType.THIRD_PLACE]
        regulars = [m for m in plan.matches if m.match_type == MatchType.REGULAR]

        assert len(finals) == 1
        assert len(semis) == 2
        assert len(thirds) == 1
        assert len(regulars) == 4

        assert all(m.match_category == MatchCategory.KNOCKOUT for m in plan.matches)

        # todos os times entram em algum confronto da primeira rodada
        first_round_team_ids = set()
        for m in regulars:
            first_round_team_ids.add(m.team1_id)
            first_round_team_ids.add(m.team2_id)
        assert first_round_team_ids == set(teams)

    def test_odd_team_count_creates_single_bye_and_resolves_winner(self):
        teams = make_team_ids(7)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})

        assert plan.byes_created == 1
        bye_matches = [m for m in plan.matches if m.is_bye]
        assert len(bye_matches) == 1

        bye_match = bye_matches[0]
        assert bye_match.status == MatchStatus.FINISHED
        assert bye_match.team2_id is None
        assert bye_match.winner_id == bye_match.team1_id
        assert bye_match.finished_at is not None

        # o vencedor do BYE já deve aparecer como um dos times da rodada seguinte
        second_round_teams = {
            m.team1_id
            for m in plan.matches
            if m.match_type == MatchType.SEMIFINAL
        } | {
            m.team2_id
            for m in plan.matches
            if m.match_type == MatchType.SEMIFINAL
        }
        assert bye_match.winner_id in second_round_teams

    def test_non_power_of_two_even_count_creates_multiple_byes(self):
        teams = make_team_ids(6)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})

        # 6 times -> próxima potência de 2 é 8 -> 2 BYEs
        assert plan.byes_created == 2
        bye_matches = [m for m in plan.matches if m.is_bye]
        assert len(bye_matches) == 2

        # nunca um BYE contra outro BYE
        for m in bye_matches:
            assert m.team1_id is not None
            assert m.team2_id is None

    def test_two_teams_final_only_no_semifinal_no_third_place(self):
        teams = make_team_ids(2)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})

        assert len(plan.matches) == 1
        assert plan.matches[0].match_type == MatchType.FINAL
        assert plan.byes_created == 0

    def test_first_round_matches_do_not_repeat_teams(self):
        teams = make_team_ids(16)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})

        seen = []
        first_round = [
            m
            for m in plan.matches
            if m.match_type == MatchType.REGULAR and m.team1_id and m.team2_id
        ]
        for m in first_round:
            seen.append(m.team1_id)
            seen.append(m.team2_id)
        assert len(seen) == len(set(seen))


class TestGroupStageKnockoutDraw:
    def test_twelve_teams_default_config(self):
        teams = make_team_ids(12)
        config = resolve_configuration(
            ModalityFormat.GROUP_STAGE_KNOCKOUT, len(teams), None
        )
        assert config["num_groups"] == 4
        assert config["classified_per_group"] == 2
        assert sum(config["group_sizes"]) == 12

        plan = build_draw(ModalityFormat.GROUP_STAGE_KNOCKOUT, teams, config)

        assert len(plan.groups) == 4
        all_group_teams = [t for g in plan.groups for t in g.team_ids]
        assert set(all_group_teams) == set(teams)

        group_matches = [m for m in plan.matches if m.match_category == MatchCategory.GROUP]
        # 4 grupos de 3 times, todos contra todos dentro do grupo: 3 partidas por grupo
        assert len(group_matches) == 4 * 3

        knockout_matches = [
            m for m in plan.matches if m.match_category == MatchCategory.KNOCKOUT
        ]
        # 8 classificados -> quartas(4) + semis(2) + final(1) + 3º lugar(1) = 8
        assert len(knockout_matches) == 8
        assert all(m.team1_id is None and m.team2_id is None for m in knockout_matches)

    def test_group_matches_linked_to_correct_group_index(self):
        teams = make_team_ids(8)
        config = resolve_configuration(
            ModalityFormat.GROUP_STAGE_KNOCKOUT, len(teams), None
        )
        plan = build_draw(ModalityFormat.GROUP_STAGE_KNOCKOUT, teams, config)

        for group_index, group in enumerate(plan.groups):
            matches_of_group = [
                m
                for m in plan.matches
                if m.match_category == MatchCategory.GROUP
                and m.group_index == group_index
            ]
            teams_in_matches = set()
            for m in matches_of_group:
                teams_in_matches.add(m.team1_id)
                teams_in_matches.add(m.team2_id)
            assert teams_in_matches == set(group.team_ids)

    def test_rejects_non_power_of_two_classification(self):
        with pytest.raises(BusinessException):
            resolve_configuration(
                ModalityFormat.GROUP_STAGE_KNOCKOUT,
                9,
                {"num_groups": 3, "classified_per_group": 1},
            )


class TestRoundRobinDraw:
    def test_even_teams_single_round(self):
        teams = make_team_ids(6)
        plan = build_draw(ModalityFormat.ROUND_ROBIN, teams, {"rounds": 1})

        # todos contra todos uma vez: C(6,2) = 15
        assert len(plan.matches) == 15
        assert all(m.match_category == MatchCategory.GROUP for m in plan.matches)
        assert len(plan.groups) == 1

        played_pairs = {frozenset((m.team1_id, m.team2_id)) for m in plan.matches}
        assert len(played_pairs) == 15

    def test_odd_teams_no_bye_match_created(self):
        teams = make_team_ids(5)
        plan = build_draw(ModalityFormat.ROUND_ROBIN, teams, {"rounds": 1})

        # C(5,2) = 10, sem partida fictícia de bye
        assert len(plan.matches) == 10
        assert all(m.team1_id is not None and m.team2_id is not None for m in plan.matches)
        assert not any(m.is_bye for m in plan.matches)

    def test_double_round_doubles_matches(self):
        teams = make_team_ids(4)
        single = build_draw(ModalityFormat.ROUND_ROBIN, teams, {"rounds": 1})
        double = build_draw(ModalityFormat.ROUND_ROBIN, teams, {"rounds": 2})

        assert len(double.matches) == len(single.matches) * 2


class TestTriangularDraw:
    def test_requires_exactly_three_teams(self):
        with pytest.raises(BusinessException):
            validate_team_count_for_format(ModalityFormat.TRIANGULAR, 4)
        with pytest.raises(BusinessException):
            validate_team_count_for_format(ModalityFormat.TRIANGULAR, 2)
        # não deve lançar para 3 times
        validate_team_count_for_format(ModalityFormat.TRIANGULAR, 3)

    def test_single_round_creates_three_matches(self):
        teams = make_team_ids(3)
        plan = build_draw(ModalityFormat.TRIANGULAR, teams, {"double_round": False})
        assert len(plan.matches) == 3
        played_pairs = {frozenset((m.team1_id, m.team2_id)) for m in plan.matches}
        assert len(played_pairs) == 3

    def test_double_round_creates_six_matches(self):
        teams = make_team_ids(3)
        plan = build_draw(ModalityFormat.TRIANGULAR, teams, {"double_round": True})
        assert len(plan.matches) == 6


class TestValidateTeamCountForFormat:
    def test_rejects_less_than_two_teams(self):
        with pytest.raises(BusinessException):
            validate_team_count_for_format(ModalityFormat.KNOCKOUT, 1)

    def test_accepts_two_or_more_for_knockout(self):
        validate_team_count_for_format(ModalityFormat.KNOCKOUT, 2)
        validate_team_count_for_format(ModalityFormat.KNOCKOUT, 30)


class TestSuggestConfiguration:
    def test_knockout_has_empty_config(self):
        assert suggest_configuration(ModalityFormat.KNOCKOUT, 10) == {}

    def test_round_robin_default_single_round(self):
        assert suggest_configuration(ModalityFormat.ROUND_ROBIN, 10) == {"rounds": 1}

    def test_triangular_default_single_round(self):
        assert suggest_configuration(ModalityFormat.TRIANGULAR, 3) == {
            "double_round": False
        }
