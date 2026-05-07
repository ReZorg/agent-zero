"""
Shared fixtures and helpers for end-to-end API tests.

These tests exercise the full HTTP API layer using Flask's test client.
No real LLM keys are required; the LLM layer is mocked where needed.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The CSRF token used by all e2e fixtures.
E2E_CSRF_TOKEN = "e2e-test-csrf-token"

# A stable auth hash used in auth-required tests.
E2E_AUTH_HASH = "e2e-test-auth-hash-abc123"


# ---------------------------------------------------------------------------
# Application fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_app() -> Flask:
    """Return a minimal Flask application with API routes registered."""
    from helpers.api import register_api_route
    from helpers import cache

    app = Flask("e2e_test_app", static_folder=None)
    app.secret_key = "e2e-test-secret-key-do-not-use-in-production"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    lock = threading.RLock()
    register_api_route(app, lock)

    # Disable the API handler cache so handlers are freshly resolved each
    # request – avoids security-decorator leakage between tests.
    cache.toggle_area("api_handlers(api)", False)

    yield app

    # Re-enable after the module finishes
    cache.toggle_area("api_handlers(api)", True)


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------

class E2EClient:
    """Thin wrapper around Flask's test client with CSRF / session helpers."""

    def __init__(self, client: FlaskClient, csrf_token: str = E2E_CSRF_TOKEN) -> None:
        self._c = client
        self._csrf = csrf_token

    # ------------------------------------------------------------------ #
    # Low-level delegates                                                  #
    # ------------------------------------------------------------------ #

    def get(self, path: str, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-CSRF-Token"] = self._csrf
        return self._c.get(path, **kwargs)

    def post(self, path: str, json: dict | None = None, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-CSRF-Token"] = self._csrf
        return self._c.post(path, json=json, **kwargs)

    def put(self, path: str, json: dict | None = None, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-CSRF-Token"] = self._csrf
        return self._c.put(path, json=json, **kwargs)

    def delete(self, path: str, json: dict | None = None, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-CSRF-Token"] = self._csrf
        return self._c.delete(path, json=json, **kwargs)

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    def api_post(self, endpoint: str, payload: dict | None = None) -> dict:
        """POST to /api/<endpoint> and return the parsed JSON body."""
        resp = self.post(f"/api/{endpoint}", json=payload or {})
        return resp.get_json() or {}

    def api_get(self, endpoint: str, payload: dict | None = None) -> dict:
        """GET to /api/<endpoint> (payload sent as JSON body) and return parsed JSON."""
        resp = self.get(f"/api/{endpoint}")
        return resp.get_json() or {}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(flask_app: Flask) -> Generator[E2EClient, None, None]:
    """Unauthenticated client with no-auth configured (no login required)."""
    with patch("helpers.login.get_credentials_hash", return_value=None), \
         patch("helpers.login.is_login_required", return_value=False):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["csrf_token"] = E2E_CSRF_TOKEN
            yield E2EClient(raw)


@pytest.fixture
def auth_client(flask_app: Flask) -> Generator[E2EClient, None, None]:
    """Authenticated client – session cookie carries a valid auth hash."""
    with patch("helpers.login.get_credentials_hash", return_value=E2E_AUTH_HASH), \
         patch("helpers.login.is_login_required", return_value=True):
        with flask_app.test_client() as raw:
            with raw.session_transaction() as sess:
                sess["csrf_token"] = E2E_CSRF_TOKEN
                sess["authentication"] = E2E_AUTH_HASH
            yield E2EClient(raw)


@pytest.fixture
def no_csrf_client(flask_app: Flask) -> Generator[FlaskClient, None, None]:
    """Raw Flask test client without CSRF token injection, for negative tests."""
    with patch("helpers.login.get_credentials_hash", return_value=None), \
         patch("helpers.login.is_login_required", return_value=False):
        with flask_app.test_client() as raw:
            yield raw


# ---------------------------------------------------------------------------
# LLM mock fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm_response():
    """
    Patch the LiteLLM / model invocation layer to return a fixed tool response.

    The mock yields a single assistant turn that calls the ``response`` tool
    with a canned message, letting agent monologue tests run without API keys.
    """
    fake_content = (
        '{"thoughts": "Test thought.", "tool_name": "response", '
        '"tool_args": {"text": "Hello from mocked LLM."}}'
    )

    async def _fake_stream(*args, **kwargs):
        class _Chunk:
            content = fake_content

        yield _Chunk()

    with patch("helpers.call_llm.call_llm", side_effect=_fake_stream):
        yield fake_content


# ---------------------------------------------------------------------------
# AgentContext cleanup
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _cleanup_agent_contexts():
    """Remove any AgentContext instances created during a test."""
    from agent import AgentContext

    before = set(AgentContext._contexts.keys())
    yield
    after = set(AgentContext._contexts.keys())
    for ctx_id in after - before:
        try:
            AgentContext.remove(ctx_id)
        except Exception:
            pass
