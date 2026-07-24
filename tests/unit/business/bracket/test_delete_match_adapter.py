from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.bracket.delete_match_adapter import DeleteMatchAdapter
from core.context import Context
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


def make_adapter():
    match_repository = AsyncMock()
    user_repository = AsyncMock()
    audit_logger = AsyncMock()
    return DeleteMatchAdapter(match_repository, user_repository, audit_logger), match_repository


class TestDeleteMatchAdapter:
    @pytest.mark.asyncio
    async def test_deletes_scheduled_match(self):
        adapter, match_repository = make_adapter()
        match = Match(id=uuid4(), status=MatchStatus.SCHEDULED)
        match_repository.get.return_value = match
        match_repository.delete.return_value = 1

        context = Context()
        context.put_property("match_id", match.id)

        result = await adapter.execute(context)

        assert result is True
        match_repository.delete.assert_awaited_once_with(match.id)

    @pytest.mark.asyncio
    async def test_blocks_when_match_not_found(self):
        adapter, match_repository = make_adapter()
        match_repository.get.return_value = None

        context = Context()
        context.put_property("match_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    @pytest.mark.asyncio
    async def test_blocks_when_match_finished(self):
        adapter, match_repository = make_adapter()
        match = Match(id=uuid4(), status=MatchStatus.FINISHED)
        match_repository.get.return_value = match

        context = Context()
        context.put_property("match_id", match.id)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        match_repository.delete.assert_not_awaited()
