from uuid import uuid4

import pytest

from domain.exceptions.business_exception import BusinessException
from security.adapters.jwt_provider_adapter import JWTProviderAdapter
from security.utils.oauth_state import (
    generate_oauth_state,
    get_platform_from_state,
    is_valid_oauth_state,
)


def test_access_token_round_trip_and_rejects_garbage():
    provider = JWTProviderAdapter()
    user_id = uuid4()
    token = provider.create_access_token(user_id, "2020123", "a@b.c").access_token

    assert provider.get_user_id_from_token(token) == user_id
    with pytest.raises(BusinessException):
        provider.verify_token(token + "x")


def test_oauth_state_round_trip():
    state = generate_oauth_state(platform="mobile")

    assert is_valid_oauth_state(state, state)
    assert get_platform_from_state(state) == "mobile"
    assert not is_valid_oauth_state(state, "other")
