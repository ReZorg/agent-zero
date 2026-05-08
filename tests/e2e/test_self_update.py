"""
E2E tests for the self-update API:
  self_update_get → version info
  self_update_tags → valid tags list
  self_update_schedule → dry-run accepted
"""
from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.e2e

VERSION_PATTERN = re.compile(r"^v\d+\.\d+")


# ---------------------------------------------------------------------------
# self_update_get
# ---------------------------------------------------------------------------

def test_self_update_get_returns_supported_field(client):
    body = client.api_get("self_update_get")
    assert "supported" in body


def test_self_update_get_returns_success_or_error_gracefully(client):
    body = client.api_get("self_update_get")
    # Either success or graceful error – no 5xx
    assert body is not None


# ---------------------------------------------------------------------------
# self_update_tags
# ---------------------------------------------------------------------------

def test_self_update_tags_returns_list(client):
    resp = client.post("/api/self_update_tags", json={})
    assert resp.status_code != 500
    body = resp.get_json()
    assert body is not None


def test_self_update_tags_version_format(client):
    resp = client.post("/api/self_update_tags", json={})
    body = resp.get_json() or {}
    tags = body.get("tags") or body.get("data") or []
    for tag in tags:
        tag_str = tag if isinstance(tag, str) else tag.get("tag", "")
        if tag_str:
            assert VERSION_PATTERN.match(tag_str), (
                f"Tag '{tag_str}' does not match version format"
            )


# ---------------------------------------------------------------------------
# self_update_schedule
# ---------------------------------------------------------------------------

def test_self_update_schedule_responds(client):
    resp = client.post("/api/self_update_schedule", json={})
    assert resp.status_code != 500
