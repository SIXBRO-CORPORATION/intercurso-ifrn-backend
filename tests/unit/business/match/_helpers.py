from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.match import Match


def make_mocks():
    return {
        "match_repository": AsyncMock(),
        "match_event_repository": AsyncMock(),
        "team_repository": AsyncMock(),
        "team_member_repository": AsyncMock(),
        "user_repository": AsyncMock(),
        "bracket_repository": AsyncMock(),
        "modality_repository": AsyncMock(),
        "modality_configuration_repository": AsyncMock(),
    }


def make_adapter(adapter_cls, mocks: dict):
    return adapter_cls(
        mocks["match_repository"],
        mocks["match_event_repository"],
        mocks["team_repository"],
        mocks["team_member_repository"],
        mocks["user_repository"],
        mocks["bracket_repository"],
        mocks["modality_repository"],
        mocks["modality_configuration_repository"],
    )


def make_in_progress_match(
    monitor_id=None,
    team1_id=None,
    team2_id=None,
    clock_seconds=100,
    clock_running=True,
    current_period=1,
    modified_at=None,
    metadata_json=None,
):
    return Match(
        id=uuid4(),
        bracket_id=uuid4(),
        team1_id=team1_id or uuid4(),
        team2_id=team2_id or uuid4(),
        monitor_id=monitor_id or uuid4(),
        match_type=MatchType.REGULAR,
        match_category=MatchCategory.KNOCKOUT,
        status=MatchStatus.IN_PROGRESS,
        team1_score=0,
        team2_score=0,
        clock_seconds=clock_seconds,
        clock_running=clock_running,
        current_period=current_period,
        modified_at=modified_at or datetime.now(),
        metadata_json=metadata_json or {},
    )


def stub_empty_management_context(mocks: dict):
    """Faz load_management_context não quebrar: repos retornam vazio/None."""
    mocks["team_repository"].get.return_value = None
    mocks["team_member_repository"].find_members_by_team_id.return_value = []
    mocks["bracket_repository"].get.return_value = None
    mocks["match_event_repository"].find_by_match.return_value = []
