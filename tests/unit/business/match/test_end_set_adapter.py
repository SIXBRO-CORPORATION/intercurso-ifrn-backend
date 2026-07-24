from uuid import uuid4

import pytest

from business.match.end_set_adapter import EndSetAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.event_type import EventType
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.match.match_set import MatchSet
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)

from tests.unit.business.match._helpers import (
    make_adapter,
    make_in_progress_match,
    make_mocks,
    stub_empty_management_context,
)


def make_context(match_id, monitor_id):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("monitor_id", monitor_id)
    return context


def setup_volleyball(mocks, match, **volleyball_overrides):
    mocks["bracket_repository"].get.return_value = Bracket(
        id=match.bracket_id, modality_id=uuid4()
    )
    mocks["modality_repository"].get.return_value = None
    mocks["modality_configuration_repository"].find_by_modality.return_value = (
        ModalityConfiguration(id=uuid4(), score_type=ScoreType.SETS)
    )
    defaults = dict(points_per_set=25, final_set_points=15, sets_to_win=2)
    defaults.update(volleyball_overrides)
    mocks[
        "volleyball_modality_configuration_repository"
    ].find_by_modality_configuration_id.return_value = VolleyballModalityConfiguration(
        **defaults
    )
    mocks["match_set_repository"].find_by_match.return_value = []
    mocks["match_set_repository"].save.side_effect = lambda match_set: match_set


class TestEndSetAdapter:
    @pytest.mark.asyncio
    async def test_end_set_rejects_non_volleyball_modality(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        mocks["match_repository"].get.return_value = match
        mocks["bracket_repository"].get.return_value = Bracket(
            id=match.bracket_id, modality_id=uuid4()
        )
        mocks["modality_repository"].get.return_value = None
        mocks["modality_configuration_repository"].find_by_modality.return_value = (
            ModalityConfiguration(score_type=ScoreType.GOALS)
        )

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_end_set_rejects_score_below_required_points(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 20
        match.team2_score = 18
        mocks["match_repository"].get.return_value = match
        setup_volleyball(mocks, match)

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_end_set_rejects_score_without_two_point_margin(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 25
        match.team2_score = 24
        mocks["match_repository"].get.return_value = match
        setup_volleyball(mocks, match)

        context = make_context(match.id, monitor_id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_end_set_accepts_25x23_and_resets_set_score(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 25
        match.team2_score = 23
        match.team1_sets_won = 0
        match.team2_sets_won = 0
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match)

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.team1_score == 0
        assert result.team2_score == 0
        assert result.team1_sets_won == 1
        assert result.team2_sets_won == 0

        saved_match_set = mocks["match_set_repository"].save.call_args[0][0]
        assert isinstance(saved_match_set, MatchSet)
        assert saved_match_set.set_number == 1
        assert saved_match_set.team1_points == 25
        assert saved_match_set.team2_points == 23
        assert saved_match_set.winner_team_id == match.team1_id

        saved_event = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.SET_END

        assert context.get_property("match_point_reached", bool) is False
        assert context.get_property("last_finished_set", MatchSet) == saved_match_set

    @pytest.mark.asyncio
    async def test_end_set_final_set_uses_final_set_points(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        # sets_to_win=2 (padrão) -> set decisivo é o 3º (2*2 - 1)
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 15
        match.team2_score = 13
        match.team1_sets_won = 1
        match.team2_sets_won = 1
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match)
        mocks["match_set_repository"].find_by_match.return_value = [
            MatchSet(match_id=match.id, set_number=1),
            MatchSet(match_id=match.id, set_number=2),
        ]

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.team1_sets_won == 2
        assert result.team2_sets_won == 1
        assert context.get_property("match_point_reached", bool) is True

        saved_match_set = mocks["match_set_repository"].save.call_args[0][0]
        assert saved_match_set.set_number == 3

    @pytest.mark.asyncio
    async def test_end_set_uses_configured_points_per_set(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 21
        match.team2_score = 19
        match.team1_sets_won = 0
        match.team2_sets_won = 0
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match, points_per_set=21)

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.team1_sets_won == 1
        assert result.team2_sets_won == 0

    @pytest.mark.asyncio
    async def test_end_set_falls_back_to_default_configuration_when_not_customized(
        self,
    ):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(monitor_id=monitor_id)
        match.team1_score = 25
        match.team2_score = 20
        match.team1_sets_won = 0
        match.team2_sets_won = 0
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m

        mocks["bracket_repository"].get.return_value = Bracket(
            id=match.bracket_id, modality_id=uuid4()
        )
        mocks["modality_repository"].get.return_value = None
        modality_configuration = ModalityConfiguration(
            id=uuid4(), score_type=ScoreType.SETS
        )
        mocks["modality_configuration_repository"].find_by_modality.return_value = (
            modality_configuration
        )
        # Nenhuma configuração de vôlei específica cadastrada ainda: o adapter
        # deve recorrer aos valores padrão (25 pontos, 15 no set decisivo,
        # melhor de 5 sets).
        mocks[
            "volleyball_modality_configuration_repository"
        ].find_by_modality_configuration_id.return_value = None
        mocks["match_set_repository"].find_by_match.return_value = []
        mocks["match_set_repository"].save.side_effect = lambda match_set: match_set

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.team1_sets_won == 1
        assert result.team2_sets_won == 0
