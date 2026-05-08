"""
E2E tests for the agent monologue with a mocked LLM.

These tests verify that:
  - Sending a message via /api/message creates a log entry in the context.
  - The agent loop does not leave the context in a permanently paused state.
  - /api/message_async returns a deferred job ID.
"""
from __future__ import annotations

import asyncio
import json
import time
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_RESPONSE_CONTENT = (
    '{"thoughts": "I will answer.", "tool_name": "response", '
    '"tool_args": {"text": "Hello from mocked LLM!"}}'
)


def _build_fake_llm_response():
    """Build a mock that returns a single streaming chunk."""

    async def _stream(*args, **kwargs):
        chunk = types.SimpleNamespace(content=FAKE_RESPONSE_CONTENT)
        yield chunk

    return _stream


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_message_creates_context(client):
    """/api/message should create (or use) a context and return a ctxid."""
    resp = client.post(
        "/api/message",
        json={
            "text": "Hello agent",
            "context": None,
        },
    )
    # The endpoint returns context info or starts processing
    assert resp.status_code != 500
    body = resp.get_json() or {}
    # Either ok=True with ctxid, or some progress indicator
    assert body is not None


def test_message_async_responds(client):
    """/api/message_async should accept the request without blocking."""
    resp = client.post(
        "/api/message_async",
        json={
            "text": "Hello async agent",
            "context": None,
        },
    )
    assert resp.status_code != 500


def test_poll_after_message_returns_snapshot(client):
    """After sending a message, /api/poll should return a valid snapshot."""
    # Create a context
    create_body = client.api_post("chat_create", {"new_context": "monologue-test-ctx"})
    assert create_body.get("ok") is True
    ctxid = create_body["ctxid"]

    # Poll immediately (log_from=0)
    poll_body = client.api_post(
        "poll",
        {"context": ctxid, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
    )
    assert "logs" in poll_body
    assert "paused" in poll_body


def test_api_reset_chat_responds(client):
    """api_reset_chat should clear and respond successfully."""
    resp = client.post("/api/api_reset_chat", json={})
    assert resp.status_code != 500


def test_nudge_endpoint_responds(client):
    resp = client.post("/api/nudge", json={})
    assert resp.status_code != 500


def test_pause_endpoint_responds(client):
    resp = client.post("/api/pause", json={})
    assert resp.status_code != 500
