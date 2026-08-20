from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket._shared import persist_draw_matches
from business.bracket.engine.draw_engine import build_draw
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat


def make_team_ids(n):
    return [uuid4() for _ in range(n)]


class TestPersistDrawMatches:
    @pytest.mark.asyncio
    async def test_next_match_id_resolves_to_the_real_persisted_id(self):
        match_repository = AsyncMock()
        match_repository.save.side_effect = lambda match: match  # eco (merge simulado)

        teams = make_team_ids(8)
        plan = build_draw(ModalityFormat.KNOCKOUT, teams, {})
        bracket_id = uuid4()

        saved_matches = await persist_draw_matches(
            match_repository, bracket_id, [], plan.matches
        )

        assert match_repository.save.await_count == len(plan.matches)
        assert all(m.bracket_id == bracket_id for m in saved_matches)

        by_type = {}
        for m in saved_matches:
            by_type.setdefault(m.match_type, []).append(m)

        final_match = by_type[MatchType.FINAL][0]
        assert final_match.next_match_id is None

        for semifinal in by_type[MatchType.SEMIFINAL]:
            assert semifinal.next_match_id == final_match.id

        semifinal_ids = {m.id for m in by_type[MatchType.SEMIFINAL]}
        for regular in by_type[MatchType.REGULAR]:
            assert regular.next_match_id in semifinal_ids

        third_place = by_type[MatchType.THIRD_PLACE][0]
        assert third_place.next_match_id is None
