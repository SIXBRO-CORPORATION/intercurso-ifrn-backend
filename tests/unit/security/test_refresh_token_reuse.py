from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from domain.auth.refresh_token import RefreshToken
from domain.exceptions.business_exception import BusinessException
from security.services.refresh_token_service import RefreshTokenService


def _service(stored):
    jwt = MagicMock()
    jwt.hash_token.return_value = "h"
    repo = AsyncMock()
    repo.find_by_token.return_value = stored
    return RefreshTokenService(jwt, repo, AsyncMock()), repo


def _token(**kw):
    return RefreshToken(
        id=uuid4(), user_id=uuid4(), token="h", active=True,
        expires_at=datetime.utcnow() + timedelta(days=1), **kw,
    )


@pytest.mark.asyncio
async def test_reusing_rotated_token_revokes_all_sessions_and_commits():
    stored = _token(revoked=True, replaced_by_token=uuid4())
    service, repo = _service(stored)

    with pytest.raises(BusinessException):
        await service.refresh_access_token("plain")

    repo.revoke_all_by_user.assert_awaited_once_with(stored.user_id)
    repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_logged_out_token_is_rejected_without_killing_other_sessions():
    service, repo = _service(_token(revoked=True))

    with pytest.raises(BusinessException):
        await service.refresh_access_token("plain")

    repo.revoke_all_by_user.assert_not_awaited()
