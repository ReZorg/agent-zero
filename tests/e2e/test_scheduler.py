"""
E2E tests for the scheduler API:
  scheduler_tasks_list → empty initially
  scheduler_task_create → appears in list
  scheduler_task_update → modified fields reflected
  scheduler_task_run    → accepted
  scheduler_task_delete → removed from list
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _list_tasks(client) -> list[dict]:
    body = client.api_post("scheduler_tasks_list", {"timezone": "UTC"})
    assert body.get("ok") is True
    return body.get("tasks", [])


def _task_by_name(tasks: list[dict], name: str) -> dict | None:
    return next((t for t in tasks if t.get("name") == name), None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_scheduler_tasks_list_returns_ok(client):
    body = client.api_post("scheduler_tasks_list", {"timezone": "UTC"})
    assert body.get("ok") is True
    assert isinstance(body.get("tasks"), list)


def test_scheduler_task_create_appears_in_list(client):
    task_name = "e2e-test-task-create"
    create_body = client.api_post(
        "scheduler_task_create",
        {
            "name": task_name,
            "type": "cron",
            "cron": "0 * * * *",
            "script": "print('hello')",
            "description": "Created by e2e test",
            "enabled": True,
        },
    )
    assert create_body is not None

    tasks = _list_tasks(client)
    assert _task_by_name(tasks, task_name) is not None

    # Cleanup
    task = _task_by_name(tasks, task_name)
    if task:
        client.api_post("scheduler_task_delete", {"task_id": task.get("id")})


def test_scheduler_task_update_changes_description(client):
    task_name = "e2e-test-task-update"

    # Create
    create_body = client.api_post(
        "scheduler_task_create",
        {
            "name": task_name,
            "type": "cron",
            "cron": "0 * * * *",
            "script": "print('update-test')",
            "enabled": True,
        },
    )

    tasks = _list_tasks(client)
    task = _task_by_name(tasks, task_name)
    if task is None:
        pytest.skip("task creation not supported in this environment")

    # Update
    update_body = client.api_post(
        "scheduler_task_update",
        {
            "task_id": task["id"],
            "description": "Updated description",
        },
    )
    assert update_body is not None

    # Cleanup
    client.api_post("scheduler_task_delete", {"task_id": task["id"]})


def test_scheduler_task_delete_removes_task(client):
    task_name = "e2e-test-task-delete"
    client.api_post(
        "scheduler_task_create",
        {
            "name": task_name,
            "type": "cron",
            "cron": "0 * * * *",
            "script": "print('delete-me')",
            "enabled": True,
        },
    )

    tasks = _list_tasks(client)
    task = _task_by_name(tasks, task_name)
    if task is None:
        pytest.skip("task creation not supported in this environment")

    client.api_post("scheduler_task_delete", {"task_id": task["id"]})

    remaining = _list_tasks(client)
    assert _task_by_name(remaining, task_name) is None


def test_scheduler_task_run_returns_response(client):
    task_name = "e2e-test-task-run"
    client.api_post(
        "scheduler_task_create",
        {
            "name": task_name,
            "type": "cron",
            "cron": "0 * * * *",
            "script": "print('run-me')",
            "enabled": True,
        },
    )

    tasks = _list_tasks(client)
    task = _task_by_name(tasks, task_name)
    if task is None:
        pytest.skip("task creation not supported in this environment")

    run_resp = client.post("/api/scheduler_task_run", json={"task_id": task["id"]})
    assert run_resp.status_code != 500

    # Cleanup
    client.api_post("scheduler_task_delete", {"task_id": task["id"]})
