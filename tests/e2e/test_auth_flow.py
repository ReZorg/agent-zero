"""
E2E tests for the authentication / login / logout flow.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

pytestmark = pytest.mark.e2e

AUTH_HASH = "sha256-test-hash"


# ---------------------------------------------------------------------------
# Login-required redirect
# ---------------------------------------------------------------------------

def test_unauthenticated_request_redirects(flask_app):
    """When auth is configured, an unauthenticated call to a protected endpoint
    returns a redirect (302) to the login page."""
    with patch("helpers.login.get_credentials_hash", return_value=AUTH_HASH), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            resp = raw.post("/api/poll", json={})
            assert resp.status_code == 302
            assert "/login" in (resp.location or "")


# ---------------------------------------------------------------------------
# Authenticated access succeeds
# ---------------------------------------------------------------------------

def test_authenticated_request_passes(flask_app):
    """When session carries the correct auth hash and CSRF token the request
    succeeds (200 or appropriate non-redirect)."""
    from tests.e2e.conftest import E2E_CSRF_TOKEN

    with patch("helpers.login.get_credentials_hash", return_value=AUTH_HASH), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["authentication"] = AUTH_HASH
                sess["csrf_token"] = E2E_CSRF_TOKEN

            resp = raw.post(
                "/api/poll",
                json={"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
                headers={"X-CSRF-Token": E2E_CSRF_TOKEN},
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Wrong auth hash is redirected
# ---------------------------------------------------------------------------

def test_wrong_auth_hash_redirects(flask_app):
    """A session with the wrong auth hash is treated as unauthenticated."""
    from tests.e2e.conftest import E2E_CSRF_TOKEN

    with patch("helpers.login.get_credentials_hash", return_value=AUTH_HASH), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["authentication"] = "wrong-hash"
                sess["csrf_token"] = E2E_CSRF_TOKEN

            resp = raw.post(
                "/api/poll",
                json={"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
                headers={"X-CSRF-Token": E2E_CSRF_TOKEN},
            )
            assert resp.status_code == 302


# ---------------------------------------------------------------------------
# No auth configured – all requests pass
# ---------------------------------------------------------------------------

def test_no_auth_configured_request_passes(flask_app):
    """When no password is configured every request should reach the handler."""
    from tests.e2e.conftest import E2E_CSRF_TOKEN

    with patch("helpers.login.get_credentials_hash", return_value=None), \
         patch("helpers.login.is_login_required", return_value=False):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["csrf_token"] = E2E_CSRF_TOKEN

            resp = raw.post(
                "/api/poll",
                json={"context": None, "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
                headers={"X-CSRF-Token": E2E_CSRF_TOKEN},
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# CSRF mismatch is rejected
# ---------------------------------------------------------------------------

def test_csrf_mismatch_returns_403(flask_app):
    """Sending a CSRF token that does not match the session token returns 403."""
    with patch("helpers.login.get_credentials_hash", return_value=None), \
         patch("helpers.login.is_login_required", return_value=False):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["csrf_token"] = "server-token"

            resp = raw.post(
                "/api/poll",
                json={},
                headers={"X-CSRF-Token": "wrong-token"},
            )
            assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Health endpoint is always open
# ---------------------------------------------------------------------------

def test_health_open_even_with_auth_configured(flask_app):
    """Health endpoint skips auth and is always accessible."""
    with patch("helpers.login.get_credentials_hash", return_value=AUTH_HASH), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            resp = raw.get("/api/health")
            assert resp.status_code == 200
