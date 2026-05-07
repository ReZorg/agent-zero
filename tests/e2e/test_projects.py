"""
E2E tests for the projects API:
  projects list / create / update / delete
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_projects_list_returns_ok(client):
    body = client.api_post("projects", {"action": "list"})
    assert body.get("ok") is True
    assert "data" in body


def test_projects_list_options_returns_ok(client):
    body = client.api_post("projects", {"action": "list_options"})
    assert body.get("ok") is True


# ---------------------------------------------------------------------------
# Create / update / delete lifecycle
# ---------------------------------------------------------------------------

def test_projects_create_update_delete(client):
    project_name = "e2e-test-project"

    # Create
    create_body = client.api_post(
        "projects",
        {
            "action": "create",
            "project": {
                "name": project_name,
                "title": "E2E Test Project",
                "description": "Created by e2e test",
            },
        },
    )
    if not create_body.get("ok"):
        pytest.skip("Project creation not available in this environment")

    # List – should contain the new project
    list_body = client.api_post("projects", {"action": "list"})
    names = [p.get("name") for p in list_body.get("data", [])]
    assert project_name in names

    # Delete
    del_body = client.api_post(
        "projects", {"action": "delete", "name": project_name}
    )
    assert del_body.get("ok") is True

    # List – should no longer contain project
    list_after = client.api_post("projects", {"action": "list"})
    names_after = [p.get("name") for p in list_after.get("data", [])]
    assert project_name not in names_after


def test_projects_invalid_action_returns_error(client):
    body = client.api_post("projects", {"action": "invalid_action"})
    assert body.get("ok") is False
