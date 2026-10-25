from uuid import uuid4

import pytest

from business.bracket._round_naming import build_round_info
from domain.enums.match_category import MatchCategory
from domain.enums.match_type import MatchType
from domain.match.match import Match


def make_match(match_type, next_match_id=None, category=MatchCategory.KNOCKOUT):
    return Match(
        id=uuid4(),
        match_type=match_type,
        match_category=category,
        next_match_id=next_match_id,
    )


@pytest.mark.unit
class TestBuildRoundInfo:
    def test_empty_matches_returns_empty_info(self):
        assert build_round_info([]) == {}

    def test_only_group_matches_returns_empty_info(self):
        group_match = make_match(MatchType.REGULAR, category=MatchCategory.GROUP)

        assert build_round_info([group_match]) == {}

    def test_final_alone_is_round_order_one(self):
        final = make_match(MatchType.FINAL)

        info = build_round_info([final])

        assert info[final.id] == ("Final", 1)

    def test_semifinal_and_final_are_named_and_ordered(self):
        final = make_match(MatchType.FINAL)
        semi1 = make_match(MatchType.SEMIFINAL, next_match_id=final.id)
        semi2 = make_match(MatchType.SEMIFINAL, next_match_id=final.id)

        info = build_round_info([final, semi1, semi2])

        assert info[final.id] == ("Final", 2)
        assert info[semi1.id] == ("Semifinal", 1)
        assert info[semi2.id] == ("Semifinal", 1)

    def test_quarterfinals_oitavas_and_deeper_rounds_get_distinct_names(self):
        final = make_match(MatchType.FINAL)
        semis = [make_match(MatchType.SEMIFINAL, next_match_id=final.id) for _ in range(2)]
        quarters = [
            make_match(MatchType.REGULAR, next_match_id=semis[i // 2].id)
            for i in range(4)
        ]
        oitavas = [
            make_match(MatchType.REGULAR, next_match_id=quarters[i // 2].id)
            for i in range(8)
        ]
        round_of_32 = [
            make_match(MatchType.REGULAR, next_match_id=oitavas[i // 2].id)
            for i in range(16)
        ]

        matches = [final, *semis, *quarters, *oitavas, *round_of_32]
        info = build_round_info(matches)

        assert info[final.id][0] == "Final"
        assert all(info[m.id][0] == "Semifinal" for m in semis)
        assert all(info[m.id][0] == "Quartas de final" for m in quarters)
        assert all(info[m.id][0] == "Oitavas de final" for m in oitavas)
        assert all(info[m.id][0] == "Rodada de 32 times" for m in round_of_32)

        # 1 = rodada mais distante da final, crescendo em direção a ela.
        assert info[round_of_32[0].id][1] == 1
        assert info[oitavas[0].id][1] == 2
        assert info[quarters[0].id][1] == 3
        assert info[semis[0].id][1] == 4
        assert info[final.id][1] == 5

    def test_third_place_gets_its_own_name_and_finals_round_order(self):
        final = make_match(MatchType.FINAL)
        semi1 = make_match(MatchType.SEMIFINAL, next_match_id=final.id)
        semi2 = make_match(MatchType.SEMIFINAL, next_match_id=final.id)
        third_place = make_match(MatchType.THIRD_PLACE)

        info = build_round_info([final, semi1, semi2, third_place])

        assert info[third_place.id] == ("Disputa de 3º lugar", info[final.id][1])

    def test_group_matches_are_not_included_in_the_result(self):
        final = make_match(MatchType.FINAL)
        group_match = make_match(MatchType.REGULAR, category=MatchCategory.GROUP)

        info = build_round_info([final, group_match])

        assert final.id in info
        assert group_match.id not in info
