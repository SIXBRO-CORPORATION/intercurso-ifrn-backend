from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.match.list_public_matches_adapter import ListPublicMatchesAdapter
from core.context import Context
from domain.exceptions.business_exception import BusinessException


def make_adapter():
    repos = [AsyncMock() for _ in range(5)]
    repos[0].search_by_season.return_value = ([], 0)
    for repo in repos[1:]:
        repo.find_by_ids.return_value = []
    return ListPublicMatchesAdapter(*repos), repos[0]


class TestListPublicMatchesAdapter:
    async def test_translates_page_into_offset_and_limit(self):
        adapter, match_repository = make_adapter()
        season_id = uuid4()
        context = Context()
        context.put_property("season_id", season_id)
        context.put_property("page", 3)
        context.put_property("size", 20)

        await adapter.execute(context)

        match_repository.search_by_season.assert_awaited_once_with(
            season_id, None, None, None, None, 40, 20
        )
        assert context.get("total") == 0

    async def test_rejects_inverted_date_range(self):
        adapter, _ = make_adapter()
        context = Context()
        context.put_property("season_id", uuid4())
        context.put_property("date_from", datetime.now())
        context.put_property("date_to", datetime.now() - timedelta(days=1))

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_requires_season(self):
        adapter, _ = make_adapter()
        with pytest.raises(BusinessException):
            await adapter.execute(Context())
