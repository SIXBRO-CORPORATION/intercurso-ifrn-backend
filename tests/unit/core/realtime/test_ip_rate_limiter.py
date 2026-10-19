import pytest

from core.realtime import ip_rate_limiter
from core.realtime.ip_rate_limiter import IpRateLimiter


@pytest.mark.unit
class TestIpRateLimiter:
    def test_blocks_after_max_requests_and_reports_retry_after(self, monkeypatch):
        now = [100.0]
        monkeypatch.setattr(ip_rate_limiter.time, "monotonic", lambda: now[0])
        limiter = IpRateLimiter(max_requests=2, window_seconds=60)

        assert limiter.allow("1.1.1.1")
        now[0] += 10
        assert limiter.allow("1.1.1.1")
        assert not limiter.allow("1.1.1.1")
        assert limiter.retry_after("1.1.1.1") == 50

    def test_allows_again_once_window_passes(self, monkeypatch):
        now = [0.0]
        monkeypatch.setattr(ip_rate_limiter.time, "monotonic", lambda: now[0])
        limiter = IpRateLimiter(max_requests=1, window_seconds=60)

        assert limiter.allow("1.1.1.1")
        assert not limiter.allow("1.1.1.1")
        now[0] += 61
        assert limiter.allow("1.1.1.1")

    def test_retry_after_is_at_least_one_second(self):
        limiter = IpRateLimiter(max_requests=1, window_seconds=60)

        assert limiter.retry_after("unknown") == 1

    def test_keys_are_independent(self):
        limiter = IpRateLimiter(max_requests=1, window_seconds=60)

        assert limiter.allow("1.1.1.1")
        assert limiter.allow("2.2.2.2")
