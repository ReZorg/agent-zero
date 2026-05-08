"""
E2E tests for the notifications API:
  notification_create → appears in notifications_history
  notifications_mark_read → marks as read
  notifications_clear → clears all
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_notifications(client) -> list[dict]:
    resp = client.post("/api/notifications_history", json={})
    body = resp.get_json() or {}
    return body.get("notifications", [])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_notifications_history_returns_list(client):
    resp = client.post("/api/notifications_history", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert "notifications" in body
    assert isinstance(body["notifications"], list)


def test_notification_create_appears_in_history(client):
    # Clear existing notifications first
    client.post("/api/notifications_clear", json={})

    # Create a notification
    resp = client.post(
        "/api/notification_create",
        json={
            "type": "info",
            "priority": "normal",
            "message": "E2E test notification",
            "title": "Test",
        },
    )
    assert resp.status_code != 500

    notifications = _get_notifications(client)
    messages = [n.get("message", "") for n in notifications]
    assert any("E2E test notification" in m for m in messages)


def test_notifications_clear_empties_history(client):
    # Create a notification to make sure there is at least one
    client.post(
        "/api/notification_create",
        json={"type": "info", "message": "Will be cleared"},
    )

    # Clear
    resp = client.post("/api/notifications_clear", json={})
    assert resp.status_code != 500

    notifications = _get_notifications(client)
    assert notifications == []


def test_notifications_mark_read_responds(client):
    # Create a notification
    client.post(
        "/api/notification_create",
        json={"type": "info", "message": "Mark-read test"},
    )

    notifications = _get_notifications(client)
    if not notifications:
        pytest.skip("No notifications to mark as read")

    notification_id = notifications[0].get("id")
    resp = client.post(
        "/api/notifications_mark_read",
        json={"notification_id": notification_id},
    )
    assert resp.status_code != 500


def test_poll_includes_notifications(client):
    """notifications array in poll snapshot should be present."""
    poll_body = client.api_post(
        "poll",
        {"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
    )
    assert "notifications" in poll_body
    assert isinstance(poll_body["notifications"], list)
    assert "notifications_version" in poll_body
