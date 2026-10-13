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


def _service_with_tokens(stored):
    service, repo = _service(stored)
    service.jwt_provider.create_token_pair.return_value = (MagicMock(), "novo")
    return service, repo


@pytest.mark.asyncio
async def test_retry_within_grace_issues_tokens_without_killing_sessions():
    original_replacement = uuid4()
    stored = _token(
        revoked=True,
        replaced_by_token=original_replacement,
        revoked_at=datetime.utcnow() - timedelta(seconds=2),
    )
    service, repo = _service_with_tokens(stored)

    _, new_plain, _ = await service.refresh_access_token("plain")

    assert new_plain == "novo"
    repo.revoke_all_by_user.assert_not_awaited()
    assert stored.replaced_by_token == original_replacement


@pytest.mark.asyncio
async def test_reuse_after_grace_still_revokes_all_sessions():
    stored = _token(
        revoked=True,
        replaced_by_token=uuid4(),
        revoked_at=datetime.utcnow() - timedelta(seconds=60),
    )
    service, repo = _service_with_tokens(stored)

    with pytest.raises(BusinessException):
        await service.refresh_access_token("plain")

    repo.revoke_all_by_user.assert_awaited_once_with(stored.user_id)
