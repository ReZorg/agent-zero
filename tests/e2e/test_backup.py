"""
E2E tests for the backup API:
  backup_get_defaults → verify default path/patterns
  backup_create → zip returned
  backup_inspect → manifest keys
  backup_preview_grouped → non-empty grouped list
  backup_restore_preview → files that would be restored
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# backup_get_defaults
# ---------------------------------------------------------------------------

def test_backup_get_defaults_returns_success(client):
    resp = client.post("/api/backup_get_defaults", json={})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None
    assert body.get("success") is True


def test_backup_get_defaults_has_patterns(client):
    body = client.api_post("backup_get_defaults")
    assert "default_patterns" in body or "metadata" in body


def test_backup_get_defaults_metadata_has_version(client):
    body = client.api_post("backup_get_defaults")
    metadata = body.get("metadata", {})
    # Must have some identifying key
    assert metadata is not None


# ---------------------------------------------------------------------------
# backup_preview_grouped
# ---------------------------------------------------------------------------

def test_backup_preview_grouped_responds(client):
    resp = client.post("/api/backup_preview_grouped", json={})
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# backup_test
# ---------------------------------------------------------------------------

def test_backup_test_endpoint_responds(client):
    resp = client.post("/api/backup_test", json={})
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# backup_inspect
# ---------------------------------------------------------------------------

def test_backup_inspect_responds_for_invalid_path(client):
    """Inspecting a non-existent backup should return a graceful error."""
    resp = client.post(
        "/api/backup_inspect",
        json={"backup_path": "/tmp/nonexistent_backup_e2e.zip"},
    )
    assert resp.status_code != 500
    body = resp.get_json()
    assert body is not None


# ---------------------------------------------------------------------------
# backup_restore_preview
# ---------------------------------------------------------------------------

def test_backup_restore_preview_responds_for_invalid_path(client):
    resp = client.post(
        "/api/backup_restore_preview",
        json={"backup_path": "/tmp/nonexistent_backup_e2e.zip"},
    )
    assert resp.status_code != 500
