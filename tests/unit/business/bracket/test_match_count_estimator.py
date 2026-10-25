from business.bracket.engine.match_count_estimator import estimate_match_counts
from domain.enums.modality_format import ModalityFormat


class TestKnockoutEstimate:
    def test_power_of_two_no_byes(self):
        result = estimate_match_counts(ModalityFormat.KNOCKOUT, 8, {"has_third_place": True})

        assert result["matches_by_round"] == [4, 2, 1]
        assert result["total_matches"] == 7

    def test_with_byes(self):
        # 5 times -> chave de 8, mesma estrutura de rodadas que 8 times
        result = estimate_match_counts(ModalityFormat.KNOCKOUT, 5, {"has_third_place": True})

        assert result["matches_by_round"] == [4, 2, 1]
        assert result["total_matches"] == 7

    def test_third_place_not_counted_in_total(self):
        with_third_place = estimate_match_counts(
            ModalityFormat.KNOCKOUT, 8, {"has_third_place": True}
        )
        without_third_place = estimate_match_counts(
            ModalityFormat.KNOCKOUT, 8, {"has_third_place": False}
        )

        assert with_third_place["total_matches"] == without_third_place["total_matches"]

    def test_two_teams(self):
        result = estimate_match_counts(ModalityFormat.KNOCKOUT, 2, {"has_third_place": False})

        assert result["matches_by_round"] == [1]
        assert result["total_matches"] == 1


class TestGroupStageKnockoutEstimate:
    def test_eight_teams_two_groups(self):
        configuration = {
            "num_groups": 2,
            "classified_per_group": 2,
            "group_sizes": [4, 4],
            "has_third_place": True,
        }

        result = estimate_match_counts(ModalityFormat.GROUP_STAGE_KNOCKOUT, 8, configuration)

        # grupos: C(4,2) + C(4,2) = 6 + 6 = 12 partidas de fase de grupos
        # mata-mata: 2 grupos x 2 classificados = 4 classificados -> semifinal(2) + final(1)
        assert result["matches_by_round"] == [12, 2, 1]
        assert result["total_matches"] == 15


class TestRoundRobinEstimate:
    def test_single_turn(self):
        result = estimate_match_counts(ModalityFormat.ROUND_ROBIN, 6, {"rounds": 1})

        assert result["matches_by_round"] == [15]
        assert result["total_matches"] == 15

    def test_double_turn(self):
        result = estimate_match_counts(ModalityFormat.ROUND_ROBIN, 6, {"rounds": 2})

        assert result["matches_by_round"] == [15, 15]
        assert result["total_matches"] == 30


class TestTriangularEstimate:
    def test_single_turn(self):
        result = estimate_match_counts(ModalityFormat.TRIANGULAR, 3, {"double_round": False})

        assert result["matches_by_round"] == [3]
        assert result["total_matches"] == 3

    def test_double_turn(self):
        result = estimate_match_counts(ModalityFormat.TRIANGULAR, 3, {"double_round": True})

        assert result["matches_by_round"] == [3, 3]
        assert result["total_matches"] == 6
