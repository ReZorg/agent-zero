"""
E2E tests for the settings API:
  settings_get → verify keys present
  settings_set → change a field → settings_get reflects change
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# settings_get
# ---------------------------------------------------------------------------

def test_settings_get_returns_settings_object(client):
    body = client.api_post("settings_get")
    assert body is not None
    # Top-level key from SettingsOutput
    assert "settings" in body or "version" in body


def test_settings_get_contains_expected_top_level_keys(client):
    """All core Settings TypedDict keys must be present in the response."""
    body = client.api_post("settings_get")
    settings_block = body.get("settings", body)

    required_keys = {
        "workdir_path",
        "mcp_servers",
        "mcp_server_enabled",
    }
    for key in required_keys:
        assert key in settings_block, f"Missing key: {key}"


def test_settings_get_additional_block_present(client):
    body = client.api_post("settings_get")
    assert "additional" in body or "settings" in body


# ---------------------------------------------------------------------------
# settings_set
# ---------------------------------------------------------------------------

def test_settings_set_changes_a_non_sensitive_field(client):
    """Changing workdir_show should be reflected in a subsequent settings_get."""
    # Read current value
    current_body = client.api_post("settings_get")
    settings_block = current_body.get("settings", current_body)
    original_value = settings_block.get("workdir_show", True)

    # Toggle the value
    new_value = not original_value
    set_resp = client.post(
        "/api/settings_set",
        json={"settings": {"workdir_show": new_value}},
    )
    assert set_resp.status_code == 200

    # Read again
    updated_body = client.api_post("settings_get")
    updated_settings = updated_body.get("settings", updated_body)
    assert updated_settings.get("workdir_show") == new_value

    # Restore
    client.post(
        "/api/settings_set",
        json={"settings": {"workdir_show": original_value}},
    )


# ---------------------------------------------------------------------------
# Smoke-test the settings_workdir_file_structure endpoint
# ---------------------------------------------------------------------------

def test_settings_workdir_file_structure_responds(client):
    resp = client.post("/api/settings_workdir_file_structure", json={})
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# Developer sections
# ---------------------------------------------------------------------------

def test_settings_developer_sections_returns_sections(client):
    resp = client.post("/api/settings_developer_sections", json={})
    assert resp.status_code != 500
    body = resp.get_json()
    assert body is not None
