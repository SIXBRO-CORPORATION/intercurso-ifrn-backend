import secrets
from datetime import datetime, timedelta

from jose import jwt, JWTError

from security.config import settings

OAUTH_STATE_COOKIE_NAME = "suap_oauth_state"
_STATE_TTL_MINUTES = 10
_STATE_TOKEN_TYPE = "oauth_state"


def generate_oauth_state() -> str:
    nonce = secrets.token_urlsafe(32)
    expire = datetime.utcnow() + timedelta(minutes=_STATE_TTL_MINUTES)

    payload = {
        "nonce": nonce,
        "typ": _STATE_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def is_valid_oauth_state(state_from_provider: str, state_from_cookie: str) -> bool:
    if not state_from_provider or not state_from_cookie:
        return False

    if not secrets.compare_digest(state_from_provider, state_from_cookie):
        return False

    try:
        payload = jwt.decode(
            state_from_cookie,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return False

    return payload.get("typ") == _STATE_TOKEN_TYPE
