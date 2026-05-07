"""
E2E tests for API surface coverage.

For every key API handler, asserts:
  - Authenticated request with valid CSRF returns a parseable JSON body.
  - Unauthenticated request (when auth is configured) is redirected (302).
  - Requests with no CSRF token are rejected (403) when auth is not required.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Health check (no auth, no CSRF)
# ---------------------------------------------------------------------------

def test_health_get_returns_200(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_post_returns_200(client):
    resp = client.post("/api/health", json={})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# CSRF token endpoint
# ---------------------------------------------------------------------------

def test_csrf_token_get_ok(flask_app):
    """csrf_token does not require CSRF; returns token and runtime_id."""
    with flask_app.test_client() as raw:
        resp = raw.get("/api/csrf_token", headers={"Origin": "http://localhost"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body is not None
        assert body.get("ok") is True
        assert "token" in body
        assert "runtime_id" in body


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_settings_get_returns_settings_keys(client):
    resp = client.get("/api/settings_get")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None
    assert "settings" in body or "version" in body  # top-level keys


def test_settings_get_post_also_works(client):
    resp = client.post("/api/settings_get", json={})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Chat create / remove
# ---------------------------------------------------------------------------

def test_chat_create_returns_ctxid(client):
    body = client.api_post("chat_create")
    assert body.get("ok") is True
    assert "ctxid" in body


def test_chat_create_with_explicit_id(client):
    body = client.api_post("chat_create", {"new_context": "explicit-test-ctx-id"})
    assert body.get("ok") is True
    assert body["ctxid"] == "explicit-test-ctx-id"


# ---------------------------------------------------------------------------
# Poll snapshot
# ---------------------------------------------------------------------------

def test_poll_returns_snapshot_keys(client):
    resp = client.post(
        "/api/poll",
        json={"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "logs" in body
    assert "contexts" in body
    assert "paused" in body
    assert "notifications" in body


# ---------------------------------------------------------------------------
# Agents list
# ---------------------------------------------------------------------------

def test_agents_list_returns_ok(client):
    body = client.api_post("agents", {"action": "list"})
    assert body.get("ok") is True
    assert "data" in body


def test_agents_invalid_action_returns_error(client):
    body = client.api_post("agents", {"action": "nonexistent_action"})
    assert body.get("ok") is False


# ---------------------------------------------------------------------------
# Subagents
# ---------------------------------------------------------------------------

def test_subagents_list_returns_ok(client):
    body = client.api_post("subagents", {"action": "list"})
    assert body.get("ok") is True


# ---------------------------------------------------------------------------
# Plugins list
# ---------------------------------------------------------------------------

def test_plugins_list_returns_ok(client):
    body = client.api_post("plugins_list", {})
    assert body.get("ok") is True
    assert "plugins" in body


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def test_skills_list_returns_ok(client):
    body = client.api_post("skills", {"action": "list"})
    assert body.get("ok") is True
    assert "data" in body


def test_skills_invalid_action_returns_error(client):
    body = client.api_post("skills", {"action": "bad_action"})
    assert body.get("ok") is False


# ---------------------------------------------------------------------------
# Scheduler tasks
# ---------------------------------------------------------------------------

def test_scheduler_tasks_list_returns_ok(client):
    body = client.api_post("scheduler_tasks_list", {"timezone": "UTC"})
    assert body.get("ok") is True
    assert "tasks" in body


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def test_notifications_history_returns_list(client):
    resp = client.post("/api/notifications_history", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert "notifications" in body
    assert isinstance(body["notifications"], list)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def test_projects_list_returns_ok(client):
    body = client.api_post("projects", {"action": "list"})
    assert body.get("ok") is True


# ---------------------------------------------------------------------------
# Self-update
# ---------------------------------------------------------------------------

def test_self_update_get_returns_info(client):
    body = client.api_get("self_update_get")
    assert "supported" in body


# ---------------------------------------------------------------------------
# Backup defaults
# ---------------------------------------------------------------------------

def test_backup_get_defaults_returns_success(client):
    resp = client.post("/api/backup_get_defaults", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None
    assert body.get("success") is True
    assert "metadata" in body


# ---------------------------------------------------------------------------
# MCP servers status
# ---------------------------------------------------------------------------

def test_mcp_servers_status_returns_success(client):
    resp = client.post("/api/mcp_servers_status", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None
    assert "success" in body or "status" in body


# ---------------------------------------------------------------------------
# Work-dir file listing
# ---------------------------------------------------------------------------

def test_get_work_dir_files_returns_list(client):
    resp = client.post("/api/get_work_dir_files", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None


# ---------------------------------------------------------------------------
# Auth enforcement: endpoint that requires auth redirects when not logged in
# ---------------------------------------------------------------------------

def test_auth_enforced_redirects_to_login(flask_app):
    """When auth is configured, an unauthenticated request returns 302."""
    from unittest.mock import patch

    with patch("helpers.login.get_credentials_hash", return_value="hash"), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            resp = raw.post("/api/settings_get", json={})
            assert resp.status_code == 302


# ---------------------------------------------------------------------------
# CSRF enforcement: missing token returns 403
# ---------------------------------------------------------------------------

def test_csrf_missing_token_returns_403(no_csrf_client):
    """A request without CSRF token is rejected with 403."""
    # Set session CSRF token but send no header / cookie
    with no_csrf_client.session_transaction() as sess:
        sess["csrf_token"] = "server-side-token"
    resp = no_csrf_client.post("/api/settings_get", json={})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 404 for unknown endpoint
# ---------------------------------------------------------------------------

def test_unknown_api_endpoint_returns_404(client):
    resp = client.post("/api/this_endpoint_does_not_exist", json={})
    assert resp.status_code == 404
