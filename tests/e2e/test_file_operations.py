"""
E2E tests for file-operation API endpoints:
  upload / download / edit / rename / delete (single + bulk)
"""
from __future__ import annotations

import io
import json
import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# work-dir file listing
# ---------------------------------------------------------------------------

def test_get_work_dir_files_responds(client):
    resp = client.get("/api/get_work_dir_files")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------

def test_upload_single_file(client):
    data = {"file": (io.BytesIO(b"hello from e2e test"), "e2e_test_file.txt")}
    resp = client.post(
        "/api/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": "e2e-test-csrf-token"},
    )
    # Should succeed (200) or give a graceful error (no 5xx)
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# edit / download
# ---------------------------------------------------------------------------

def test_edit_work_dir_file_responds(client):
    resp = client.post(
        "/api/edit_work_dir_file",
        json={"path": "e2e_edit_test.txt", "content": "edited content"},
    )
    assert resp.status_code != 500


def test_download_work_dir_file_responds(client):
    # Create the file first via edit
    client.post(
        "/api/edit_work_dir_file",
        json={"path": "e2e_download_test.txt", "content": "downloadable"},
    )
    resp = client.post(
        "/api/download_work_dir_file",
        json={"path": "e2e_download_test.txt"},
    )
    # 200 (file download) or a JSON error – not a 5xx
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# rename
# ---------------------------------------------------------------------------

def test_rename_work_dir_file_responds(client):
    # Create a file, then rename it
    client.post(
        "/api/edit_work_dir_file",
        json={"path": "e2e_rename_src.txt", "content": "rename me"},
    )
    resp = client.post(
        "/api/rename_work_dir_file",
        json={"path": "e2e_rename_src.txt", "new_path": "e2e_rename_dst.txt"},
    )
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# delete (single)
# ---------------------------------------------------------------------------

def test_delete_work_dir_file_responds(client):
    # Create a file, then delete it
    client.post(
        "/api/edit_work_dir_file",
        json={"path": "e2e_delete_me.txt", "content": "delete me"},
    )
    resp = client.post(
        "/api/delete_work_dir_file",
        json={"path": "e2e_delete_me.txt"},
    )
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# delete (bulk)
# ---------------------------------------------------------------------------

def test_delete_work_dir_files_bulk_responds(client):
    # Create two files
    for name in ["e2e_bulk_1.txt", "e2e_bulk_2.txt"]:
        client.post(
            "/api/edit_work_dir_file",
            json={"path": name, "content": "bulk delete"},
        )

    resp = client.post(
        "/api/delete_work_dir_files",
        json={"paths": ["e2e_bulk_1.txt", "e2e_bulk_2.txt"]},
    )
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# file_info
# ---------------------------------------------------------------------------

def test_file_info_responds(client):
    resp = client.post("/api/file_info", json={"path": "usr/settings.json"})
    assert resp.status_code != 500
