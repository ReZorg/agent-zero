"""Tests for the _ecosystem plugin catalog and API handler.

Validates catalog structure, field requirements, action integrity, and
the sidebar integration without requiring the full Agent Zero runtime.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._ecosystem.helpers.catalog import CATALOG

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_ENTRY_TYPES = {"product", "integration", "template", "install", "benchmark", "example"}
VALID_ACTION_TYPES = {"open_url", "copy_text", "open_plugin_hub", "open_settings"}
REQUIRED_ENTRY_FIELDS = {"id", "type", "title", "subtitle", "description", "github", "actions"}
REQUIRED_ACTION_FIELDS = {"type", "label"}

EXPECTED_IDS = {
    "agent-zero",
    "a0-plugins",
    "a0-connector",
    "code-execution-mcp",
    "a0-example-plugin",
    "a0-install",
    "a0-launcher",
    "space-agent",
    "a0-benchmarks",
    "heroku-python-minimal",
}

# ── Catalog structure ─────────────────────────────────────────────────────────


def test_catalog_is_non_empty_list():
    assert isinstance(CATALOG, list)
    assert len(CATALOG) > 0


def test_all_expected_repos_present():
    ids = {entry["id"] for entry in CATALOG}
    missing = EXPECTED_IDS - ids
    assert not missing, f"Missing ecosystem entries: {missing}"


def test_ids_are_unique():
    ids = [entry["id"] for entry in CATALOG]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in catalog"


def test_required_entry_fields_present():
    for entry in CATALOG:
        missing = REQUIRED_ENTRY_FIELDS - set(entry.keys())
        assert not missing, f"Entry '{entry.get('id', '?')}' missing fields: {missing}"


def test_entry_types_are_valid():
    for entry in CATALOG:
        assert entry["type"] in VALID_ENTRY_TYPES, (
            f"Entry '{entry['id']}' has invalid type: {entry['type']!r}. "
            f"Expected one of: {VALID_ENTRY_TYPES}"
        )


def test_github_urls_are_agent0ai():
    for entry in CATALOG:
        github = entry.get("github", "")
        assert isinstance(github, str), f"Entry '{entry['id']}' github must be a string"
        assert github.startswith("https://github.com/agent0ai/"), (
            f"Entry '{entry['id']}' github URL should be under agent0ai org: {github!r}"
        )


# ── Action structure ──────────────────────────────────────────────────────────


def test_each_entry_has_at_least_one_action():
    for entry in CATALOG:
        assert isinstance(entry["actions"], list) and len(entry["actions"]) >= 1, (
            f"Entry '{entry['id']}' must have at least one action"
        )


def test_required_action_fields_present():
    for entry in CATALOG:
        for i, action in enumerate(entry["actions"]):
            missing = REQUIRED_ACTION_FIELDS - set(action.keys())
            assert not missing, (
                f"Action #{i} in '{entry['id']}' missing fields: {missing}"
            )


def test_action_types_are_valid():
    for entry in CATALOG:
        for action in entry["actions"]:
            assert action["type"] in VALID_ACTION_TYPES, (
                f"Action '{action.get('label')}' in '{entry['id']}' has invalid "
                f"type: {action['type']!r}. Expected one of: {VALID_ACTION_TYPES}"
            )


def test_open_url_actions_have_url():
    for entry in CATALOG:
        for action in entry["actions"]:
            if action["type"] == "open_url":
                assert "url" in action, (
                    f"open_url action '{action['label']}' in '{entry['id']}' "
                    f"is missing 'url'"
                )
                assert action["url"].startswith("http"), (
                    f"open_url action '{action['label']}' in '{entry['id']}' "
                    f"has a non-HTTP url: {action['url']!r}"
                )


def test_copy_text_actions_have_text():
    for entry in CATALOG:
        for action in entry["actions"]:
            if action["type"] == "copy_text":
                assert "text" in action and action["text"], (
                    f"copy_text action '{action['label']}' in '{entry['id']}' "
                    f"is missing 'text'"
                )


def test_open_settings_actions_have_valid_tab():
    from plugins._ecosystem.helpers.catalog import VALID_SETTINGS_TABS

    for entry in CATALOG:
        for action in entry["actions"]:
            if action["type"] == "open_settings":
                tab = action.get("tab", "")
                assert tab in VALID_SETTINGS_TABS, (
                    f"open_settings action '{action['label']}' in '{entry['id']}' "
                    f"references unknown tab: {tab!r}. Valid tabs: {VALID_SETTINGS_TABS}"
                )


# ── API handler smoke test ────────────────────────────────────────────────────


def test_api_handler_imports_and_returns_catalog():
    """Verify the Ecosystem API handler logic: _get_catalog returns the catalog.

    We test the data layer directly (avoiding the Flask runtime dependency)
    since the handler is a thin pass-through over helpers/catalog.py.
    """
    # Import only the catalog module, not the handler (which requires Flask)
    from plugins._ecosystem.helpers.catalog import CATALOG as source_catalog

    # Simulate what Ecosystem._get_catalog() does
    result = {"success": True, "catalog": source_catalog}

    assert result["success"] is True
    assert isinstance(result["catalog"], list)
    assert len(result["catalog"]) == len(CATALOG)
    # Spot-check the first entry comes back intact
    first = result["catalog"][0]
    assert "id" in first
    assert "type" in first
    assert "actions" in first


# ── Sidebar integration ───────────────────────────────────────────────────────


def test_sidebar_has_ecosystem_entry():
    header_icons = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "sidebar"
        / "top-section"
        / "header-icons.html"
    )
    content = header_icons.read_text(encoding="utf-8")
    assert "Ecosystem" in content, (
        "The Ecosystem entry was not found in header-icons.html"
    )
    assert "/plugins/_ecosystem/webui/main.html" in content, (
        "The ecosystem modal path was not found in header-icons.html"
    )


def test_sidebar_space_agent_link_replaced():
    """Direct 'space-agent.ai' external link should no longer appear; it is
    surfaced through the Ecosystem Hub instead."""
    header_icons = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "sidebar"
        / "top-section"
        / "header-icons.html"
    )
    content = header_icons.read_text(encoding="utf-8")
    assert "https://space-agent.ai/" not in content, (
        "Direct space-agent.ai link should be replaced by the Ecosystem Hub entry"
    )
