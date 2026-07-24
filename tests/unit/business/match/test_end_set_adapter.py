from uuid import uuid4

import pytest

from business.match.end_set_adapter import EndSetAdapter
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.event_type import EventType
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality_configuration import ModalityConfiguration

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


def setup_volleyball(mocks, match, config_metadata=None):
    mocks["bracket_repository"].get.return_value = Bracket(
        id=match.bracket_id, modality_id=uuid4()
    )
    mocks["modality_repository"].get.return_value = None
    mocks["modality_configuration_repository"].find_by_modality.return_value = (
        ModalityConfiguration(score_type=ScoreType.SETS, metadata=config_metadata or {})
    )


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
        match = make_in_progress_match(
            monitor_id=monitor_id,
            metadata_json={
                "current_set_score": {"team1": 20, "team2": 18},
                "current_set_number": 1,
            },
        )
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
        match = make_in_progress_match(
            monitor_id=monitor_id,
            metadata_json={
                "current_set_score": {"team1": 25, "team2": 24},
                "current_set_number": 1,
            },
        )
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
        match = make_in_progress_match(
            monitor_id=monitor_id,
            metadata_json={
                "current_set_score": {"team1": 25, "team2": 23},
                "current_set_number": 1,
                "sets": [],
                "sets_won": {"team1": 0, "team2": 0},
            },
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match)

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.metadata_json["current_set_score"] == {"team1": 0, "team2": 0}
        assert result.metadata_json["current_set_number"] == 2
        assert result.metadata_json["sets_won"] == {"team1": 1, "team2": 0}
        assert len(result.metadata_json["sets"]) == 1
        assert result.metadata_json["sets"][0]["score"] == "25x23"

        saved_event = mocks["match_event_repository"].save.call_args[0][0]
        assert saved_event.event_type == EventType.SET_END

        assert context.get("match_point_reached") is False

    @pytest.mark.asyncio
    async def test_end_set_final_set_uses_15_points(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        # sets_to_win=2 (padrão) -> set decisivo é o 3º (2*2 - 1)
        match = make_in_progress_match(
            monitor_id=monitor_id,
            metadata_json={
                "current_set_score": {"team1": 15, "team2": 13},
                "current_set_number": 3,
                "sets": [],
                "sets_won": {"team1": 1, "team2": 1},
            },
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match)

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.metadata_json["sets_won"] == {"team1": 2, "team2": 1}
        assert context.get("match_point_reached") is True

    @pytest.mark.asyncio
    async def test_end_set_uses_configured_points_per_set(self):
        mocks = make_mocks()
        adapter = make_adapter(EndSetAdapter, mocks)
        stub_empty_management_context(mocks)

        monitor_id = uuid4()
        match = make_in_progress_match(
            monitor_id=monitor_id,
            metadata_json={
                "current_set_score": {"team1": 21, "team2": 19},
                "current_set_number": 1,
                "sets": [],
                "sets_won": {"team1": 0, "team2": 0},
            },
        )
        mocks["match_repository"].get.return_value = match
        mocks["match_repository"].save.side_effect = lambda m: m
        setup_volleyball(mocks, match, config_metadata={"points_per_set": 21})

        context = make_context(match.id, monitor_id)
        result = await adapter.execute(context)

        assert result.metadata_json["sets_won"] == {"team1": 1, "team2": 0}
