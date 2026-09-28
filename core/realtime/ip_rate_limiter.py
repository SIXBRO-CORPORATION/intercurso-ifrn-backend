from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

DEFAULT_MAX_REQUESTS = 10
DEFAULT_WINDOW_SECONDS = 60.0


class IpRateLimiter:
    def __init__(
        self,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self._window_seconds:
            hits.popleft()
        if len(hits) >= self._max_requests:
            return False
        hits.append(now)
        return True


_anonymous_ticket_rate_limiter: IpRateLimiter | None = None


def get_anonymous_ticket_rate_limiter_singleton() -> IpRateLimiter:
    global _anonymous_ticket_rate_limiter
    if _anonymous_ticket_rate_limiter is None:
        _anonymous_ticket_rate_limiter = IpRateLimiter()
    return _anonymous_ticket_rate_limiter
