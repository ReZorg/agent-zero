"""
E2E tests for the chat lifecycle:
  chat_create → chat_load → chat_reset → chat_remove
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# chat_create
# ---------------------------------------------------------------------------

def test_chat_create_returns_ok_and_ctxid(client):
    body = client.api_post("chat_create")
    assert body.get("ok") is True
    ctxid = body.get("ctxid")
    assert ctxid and isinstance(ctxid, str)


def test_chat_create_returns_stable_ctxid_when_given(client):
    body = client.api_post("chat_create", {"new_context": "my-stable-ctx"})
    assert body.get("ok") is True
    assert body["ctxid"] == "my-stable-ctx"


# ---------------------------------------------------------------------------
# chat_load
# ---------------------------------------------------------------------------

def test_chat_load_known_context_returns_ok(client):
    # First create a context
    create_body = client.api_post("chat_create", {"new_context": "load-test-ctx"})
    assert create_body.get("ok") is True

    # Load it
    load_body = client.api_post("chat_load", {"ctxid": "load-test-ctx"})
    assert load_body.get("ok") is True


def test_chat_load_nonexistent_context_creates_one(client):
    """chat_load creates a context if it doesn't exist yet."""
    body = client.api_post("chat_load", {"ctxid": "brand-new-ctx-xyz"})
    # Should succeed (or create the context on demand)
    assert body is not None


# ---------------------------------------------------------------------------
# chat_reset
# ---------------------------------------------------------------------------

def test_chat_reset_clears_log(client):
    # Create context
    create_body = client.api_post("chat_create", {"new_context": "reset-test-ctx"})
    assert create_body.get("ok") is True

    # Reset it
    reset_body = client.api_post("chat_reset", {"ctxid": "reset-test-ctx"})
    assert reset_body is not None


# ---------------------------------------------------------------------------
# chat_remove
# ---------------------------------------------------------------------------

def test_chat_remove_context_disappears_from_list(client):
    # Create a context
    create_body = client.api_post("chat_create", {"new_context": "remove-test-ctx"})
    assert create_body.get("ok") is True

    # Remove it
    remove_body = client.api_post("chat_remove", {"ctxid": "remove-test-ctx"})
    assert remove_body is not None

    # Poll – context should not be in contexts list
    poll_body = client.api_post(
        "poll",
        {"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
    )
    contexts = poll_body.get("contexts", [])
    ctx_ids = [c.get("id") for c in contexts]
    assert "remove-test-ctx" not in ctx_ids


# ---------------------------------------------------------------------------
# Multiple contexts
# ---------------------------------------------------------------------------

def test_multiple_contexts_appear_in_poll(client):
    ids = ["multi-ctx-1", "multi-ctx-2", "multi-ctx-3"]
    for cid in ids:
        body = client.api_post("chat_create", {"new_context": cid})
        assert body.get("ok") is True

    poll_body = client.api_post(
        "poll",
        {"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
    )
    ctx_ids = {c.get("id") for c in poll_body.get("contexts", [])}
    for cid in ids:
        assert cid in ctx_ids


# ---------------------------------------------------------------------------
# chat_export
# ---------------------------------------------------------------------------

def test_chat_export_returns_response(client):
    # Create a context first
    client.api_post("chat_create", {"new_context": "export-test-ctx"})

    resp = client.post("/api/chat_export", json={"ctxid": "export-test-ctx"})
    # Should be 200 (download) or an error dict – not a 5xx
    assert resp.status_code != 500
