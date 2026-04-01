"""Tests for helpers/rate_limiter.py – the async RateLimiter class."""
import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from helpers.rate_limiter import RateLimiter


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_timeframe(self):
        rl = RateLimiter()
        assert rl.timeframe == 60

    def test_custom_timeframe(self):
        rl = RateLimiter(seconds=30)
        assert rl.timeframe == 30

    def test_limits_stored(self):
        rl = RateLimiter(seconds=60, requests=10, tokens=1000)
        assert rl.limits["requests"] == 10
        assert rl.limits["tokens"] == 1000

    def test_values_initialized_for_each_limit(self):
        rl = RateLimiter(seconds=60, requests=5)
        assert "requests" in rl.values
        assert rl.values["requests"] == []

    def test_non_numeric_limit_stored_as_zero(self):
        rl = RateLimiter(seconds=60, requests="bad")  # type: ignore[arg-type]
        assert rl.limits["requests"] == 0

    def test_no_limits(self):
        rl = RateLimiter(seconds=60)
        assert rl.limits == {}


# ---------------------------------------------------------------------------
# add / get_total
# ---------------------------------------------------------------------------

class TestAddAndGetTotal:
    @pytest.mark.asyncio
    async def test_add_single_value(self):
        rl = RateLimiter(seconds=60, requests=100)
        rl.add(requests=1)
        total = await rl.get_total("requests")
        assert total == 1

    @pytest.mark.asyncio
    async def test_add_accumulates(self):
        rl = RateLimiter(seconds=60, requests=100)
        rl.add(requests=3)
        rl.add(requests=7)
        total = await rl.get_total("requests")
        assert total == 10

    @pytest.mark.asyncio
    async def test_add_unknown_key_creates_entry(self):
        rl = RateLimiter(seconds=60)
        rl.add(newkey=5)
        total = await rl.get_total("newkey")
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_total_missing_key_returns_zero(self):
        rl = RateLimiter(seconds=60)
        total = await rl.get_total("nonexistent")
        assert total == 0

    @pytest.mark.asyncio
    async def test_add_multiple_keys_at_once(self):
        rl = RateLimiter(seconds=60, requests=100, tokens=1000)
        rl.add(requests=2, tokens=50)
        assert await rl.get_total("requests") == 2
        assert await rl.get_total("tokens") == 50


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_removes_old_entries(self):
        rl = RateLimiter(seconds=1)  # 1-second window
        rl.add(requests=5)
        # Manually back-date the entry so it looks old
        rl.values["requests"][0] = (time.time() - 2, 5)
        await rl.cleanup()
        assert await rl.get_total("requests") == 0

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_entries(self):
        rl = RateLimiter(seconds=60)
        rl.add(requests=3)
        await rl.cleanup()
        assert await rl.get_total("requests") == 3

    @pytest.mark.asyncio
    async def test_cleanup_partial_expiry(self):
        rl = RateLimiter(seconds=5)
        # One old entry, one fresh
        rl.values["requests"] = [(time.time() - 10, 2), (time.time(), 1)]
        await rl.cleanup()
        assert await rl.get_total("requests") == 1


# ---------------------------------------------------------------------------
# wait – no limit exceeded (should return immediately)
# ---------------------------------------------------------------------------

class TestWaitUnderLimit:
    @pytest.mark.asyncio
    async def test_wait_returns_immediately_when_under_limit(self):
        rl = RateLimiter(seconds=60, requests=100)
        rl.add(requests=10)
        # Should complete almost instantly
        start = time.monotonic()
        await rl.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0  # well under any blocking threshold

    @pytest.mark.asyncio
    async def test_wait_returns_immediately_with_no_limits(self):
        rl = RateLimiter(seconds=60)
        rl.add(requests=99999)
        start = time.monotonic()
        await rl.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_wait_returns_immediately_with_limit_zero(self):
        rl = RateLimiter(seconds=60, requests=0)
        rl.add(requests=1000)
        start = time.monotonic()
        await rl.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0


# ---------------------------------------------------------------------------
# wait – limit exceeded triggers callback
# ---------------------------------------------------------------------------

class TestWaitOverLimit:
    @pytest.mark.asyncio
    async def test_callback_called_when_limit_exceeded(self):
        rl = RateLimiter(seconds=60, requests=5)
        rl.add(requests=10)  # Over limit

        calls = []

        async def callback(msg, key, total, limit):
            calls.append((key, total, limit))
            # Return True to indicate "continue anyway" (skip waiting)
            return True

        await rl.wait(callback=callback)
        assert len(calls) >= 1
        key, total, limit = calls[0]
        assert key == "requests"
        assert total > limit

    @pytest.mark.asyncio
    async def test_callback_receives_correct_key_and_values(self):
        rl = RateLimiter(seconds=60, tokens=100)
        rl.add(tokens=200)

        recorded = {}

        async def callback(msg, key, total, limit):
            recorded.update({"key": key, "total": total, "limit": limit})
            return True  # allow proceeding

        await rl.wait(callback=callback)
        assert recorded["key"] == "tokens"
        assert recorded["total"] > recorded["limit"]

    @pytest.mark.asyncio
    async def test_callback_message_is_string(self):
        rl = RateLimiter(seconds=60, requests=1)
        rl.add(requests=2)

        messages = []

        async def callback(msg, key, total, limit):
            messages.append(msg)
            return True

        await rl.wait(callback=callback)
        assert messages
        assert isinstance(messages[0], str)
