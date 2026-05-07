"""
E2E tests for the plugins API:
  plugins_list → returns list with required fields
  toggling a plugin
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# plugins_list
# ---------------------------------------------------------------------------

def test_plugins_list_returns_ok(client):
    body = client.api_post("plugins_list", {})
    assert body.get("ok") is True
    assert "plugins" in body


def test_plugins_list_entries_have_required_fields(client):
    body = client.api_post("plugins_list", {})
    plugins = body.get("plugins", [])
    # May be empty in minimal test env – just verify structure when present
    for plugin in plugins:
        assert "name" in plugin, f"Plugin missing 'name': {plugin}"


def test_plugins_list_custom_filter_responds(client):
    body = client.api_post("plugins_list", {"filter": {"custom": True, "builtin": False}})
    assert body.get("ok") is True


def test_plugins_list_builtin_filter_responds(client):
    body = client.api_post("plugins_list", {"filter": {"custom": False, "builtin": True}})
    assert body.get("ok") is True


# ---------------------------------------------------------------------------
# load_webui_extensions
# ---------------------------------------------------------------------------

def test_load_webui_extensions_responds(client):
    resp = client.post("/api/load_webui_extensions", json={})
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# plugins endpoint (legacy)
# ---------------------------------------------------------------------------

def test_plugins_endpoint_responds(client):
    resp = client.post("/api/plugins", json={})
    assert resp.status_code != 500
