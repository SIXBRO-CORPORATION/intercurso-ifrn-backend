from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.draw_knockout_stage_adapter import DrawKnockoutStageAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


def make_adapter():
    bracket_repository = AsyncMock()
    bracket_group_repository = AsyncMock()
    bracket_group_team_repository = AsyncMock()
    match_repository = AsyncMock()
    audit_logger = AsyncMock()

    match_repository.lock_for_update.side_effect = lambda match_id: next(
        (m for m in match_repository._all_matches if m.id == match_id), None
    )

    adapter = DrawKnockoutStageAdapter(
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        audit_logger,
    )
    return (
        adapter,
        bracket_repository,
        bracket_group_repository,
        bracket_group_team_repository,
        match_repository,
        audit_logger,
    )


def make_bracket(classified_per_group=2, num_groups=2, bracket_format=ModalityFormat.GROUP_STAGE_KNOCKOUT):
    return Bracket(
        id=uuid4(),
        season_id=uuid4(),
        modality_id=uuid4(),
        format=bracket_format,
        configuration={
            "num_groups": num_groups,
            "classified_per_group": classified_per_group,
            "group_sizes": [3] * num_groups,
        },
        status=BracketStatus.ACTIVE,
        created_by=uuid4(),
    )


def build_scenario(num_groups=2, classified_per_group=2, team_per_group=3):
    """Monta 2 grupos completos (times, partidas finalizadas, standings) e o
    esqueleto de mata-mata (times TBD), pronto pra ser sorteado."""
    groups = [
        BracketGroup(id=uuid4(), bracket_id=uuid4(), name=f"Grupo {i}", display_order=i)
        for i in range(num_groups)
    ]

    teams_by_group = {}
    matches = []
    for group in groups:
        team_ids = [uuid4() for _ in range(team_per_group)]
        teams_by_group[group.id] = [
            BracketGroupTeam(
                id=uuid4(),
                bracket_group_id=group.id,
                team_id=team_id,
                points=(team_per_group - idx) * 3,
                wins=team_per_group - idx,
                draws=0,
                losses=0,
                goals_for=0,
                goals_against=0,
                goals_difference=0,
            )
            for idx, team_id in enumerate(team_ids)
        ]
        matches.append(
            Match(
                id=uuid4(),
                bracket_group_id=group.id,
                team1_id=team_ids[0],
                team2_id=team_ids[1],
                team1_score=1,
                team2_score=0,
                winner_id=team_ids[0],
                status=MatchStatus.FINISHED,
                match_category=MatchCategory.GROUP,
            )
        )

    total_classified = num_groups * classified_per_group
    quarters = [
        Match(
            id=uuid4(),
            match_category=MatchCategory.KNOCKOUT,
            match_type=MatchType.REGULAR,
            status=MatchStatus.SCHEDULED,
        )
        for _ in range(total_classified // 2)
    ]
    third_place = Match(
        id=uuid4(),
        match_category=MatchCategory.KNOCKOUT,
        match_type=MatchType.THIRD_PLACE,
        status=MatchStatus.SCHEDULED,
    )
    matches = matches + quarters + [third_place]

    return groups, teams_by_group, matches, quarters


class TestDrawKnockoutStageAdapter:
    @pytest.mark.asyncio
    async def test_draws_and_fills_first_round_slots(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            audit_logger,
        ) = make_adapter()

        bracket = make_bracket(classified_per_group=2, num_groups=2)
        groups, teams_by_group, matches, quarters = build_scenario(
            num_groups=2, classified_per_group=2
        )

        bracket_repository.get.return_value = bracket
        match_repository.find_by_bracket.return_value = matches
        match_repository._all_matches = matches
        bracket_group_repository.find_by_bracket.return_value = groups
        bracket_group_team_repository.find_by_groups.return_value = [
            team for teams in teams_by_group.values() for team in teams
        ]

        context = Context()
        context.put_property("bracket_id", bracket.id)
        context.put_property("requested_by", uuid4())

        result = await adapter.execute(context)

        assert result is bracket
        assert all(q.team1_id is not None and q.team2_id is not None for q in quarters)
        all_assigned = {q.team1_id for q in quarters} | {q.team2_id for q in quarters}
        assert len(all_assigned) == 4  # 2 grupos x 2 classificados, sem repetição
        audit_logger.log.assert_awaited_once()
        assert context.get_property("classified_count", int) == 4
        assert context.get_property("knockout_matches_filled", int) == 2

    @pytest.mark.asyncio
    async def test_rejects_when_bracket_is_not_group_stage_knockout(self):
        (adapter, bracket_repository, *_rest) = make_adapter()
        bracket = make_bracket(bracket_format=ModalityFormat.KNOCKOUT)
        bracket_repository.get.return_value = bracket

        context = Context()
        context.put_property("bracket_id", bracket.id)
        context.put_property("requested_by", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_rejects_when_group_matches_still_pending(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            _audit_logger,
        ) = make_adapter()

        bracket = make_bracket()
        _, _, matches, _ = build_scenario()
        matches[0].status = MatchStatus.IN_PROGRESS

        bracket_repository.get.return_value = bracket
        match_repository.find_by_bracket.return_value = matches

        context = Context()
        context.put_property("bracket_id", bracket.id)
        context.put_property("requested_by", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_rejects_when_already_drawn(self):
        (
            adapter,
            bracket_repository,
            bracket_group_repository,
            bracket_group_team_repository,
            match_repository,
            _audit_logger,
        ) = make_adapter()

        bracket = make_bracket()
        _, _, matches, quarters = build_scenario()
        quarters[0].team1_id = uuid4()  # já sorteado antes

        bracket_repository.get.return_value = bracket
        match_repository.find_by_bracket.return_value = matches

        context = Context()
        context.put_property("bracket_id", bracket.id)
        context.put_property("requested_by", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_rejects_when_bracket_not_found(self):
        (adapter, bracket_repository, *_rest) = make_adapter()
        bracket_repository.get.return_value = None

        context = Context()
        context.put_property("bracket_id", uuid4())
        context.put_property("requested_by", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)
