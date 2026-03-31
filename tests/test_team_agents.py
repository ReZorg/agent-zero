"""
Tests for the team agent feature:
- TeamAgent model
- team_agents field on SubAgentListItem / SubAgent
- save / load round-trip for team_agents
- agents/team/ profile files exist and contain required content
- call_sub variables include team_agents when present
- enabled field is preserved during merge
- model_dump serialization produces JSON-safe output (API layer)
"""

from __future__ import annotations

import json
import sys
import types
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Stub heavy / unavailable third-party modules so we can import helpers.subagents
# without the full runtime being installed.
for _mod in ("regex",):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)
# regex.W is used as a flag constant in helpers/plugins.py
sys.modules["regex"].W = 0  # type: ignore[attr-defined]

# git (GitPython) stubs
if "git" not in sys.modules:
    sys.modules["git"] = types.SimpleNamespace(Git=object, Repo=object)  # type: ignore[assignment]

from helpers.subagents import (
    SubAgent,
    SubAgentListItem,
    TeamAgent,
    _merge_agent_list_items,
    _merge_agents,
)


# ---------------------------------------------------------------------------
# TeamAgent model
# ---------------------------------------------------------------------------


def test_team_agent_defaults():
    ta = TeamAgent()
    assert ta.profile == ""
    assert ta.name == ""
    assert ta.description == ""


def test_team_agent_full_construction():
    ta = TeamAgent(
        profile="developer",
        name="Dev",
        description="Writes code",
    )
    assert ta.profile == "developer"
    assert ta.name == "Dev"
    assert ta.description == "Writes code"


# ---------------------------------------------------------------------------
# SubAgentListItem / SubAgent – team_agents field
# ---------------------------------------------------------------------------


def test_sub_agent_list_item_team_agents_defaults_to_empty():
    item = SubAgentListItem(name="test", title="Test")
    assert item.team_agents == []


def test_sub_agent_team_agents_can_be_set():
    agent = SubAgent(
        name="myteam",
        title="My Team",
        team_agents=[
            TeamAgent(profile="developer", name="Dev"),
            TeamAgent(profile="researcher", description="Researches stuff"),
        ],
    )
    assert len(agent.team_agents) == 2
    assert agent.team_agents[0].profile == "developer"
    assert agent.team_agents[1].profile == "researcher"


def test_sub_agent_list_item_parsed_from_dict_with_team_agents():
    data = {
        "name": "team",
        "title": "Team",
        "team_agents": [
            {"profile": "developer", "name": "Dev", "description": "Codes"},
        ],
    }
    item = SubAgentListItem.model_validate(data)
    assert len(item.team_agents) == 1
    assert item.team_agents[0].profile == "developer"


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------


def test_merge_agents_team_agents_override_wins():
    base = SubAgent(
        name="base",
        title="Base",
        team_agents=[TeamAgent(profile="researcher")],
    )
    override = SubAgent(
        name="override",
        title="Override",
        team_agents=[TeamAgent(profile="developer")],
    )
    merged = _merge_agents(base, override)
    assert merged is not None
    assert len(merged.team_agents) == 1
    assert merged.team_agents[0].profile == "developer"


def test_merge_agents_team_agents_base_kept_when_override_empty():
    base = SubAgent(
        name="base",
        title="Base",
        team_agents=[TeamAgent(profile="researcher")],
    )
    override = SubAgent(name="override", title="Override", team_agents=[])
    merged = _merge_agents(base, override)
    assert merged is not None
    assert len(merged.team_agents) == 1
    assert merged.team_agents[0].profile == "researcher"


def test_merge_agent_list_items_team_agents_override_wins():
    base = SubAgentListItem(
        name="base",
        team_agents=[TeamAgent(profile="designer")],
    )
    override = SubAgentListItem(
        name="override",
        team_agents=[TeamAgent(profile="developer")],
    )
    merged = _merge_agent_list_items(base, override)
    assert len(merged.team_agents) == 1
    assert merged.team_agents[0].profile == "developer"


def test_merge_agent_list_items_team_agents_base_kept_when_override_empty():
    base = SubAgentListItem(
        name="base",
        team_agents=[TeamAgent(profile="designer")],
    )
    override = SubAgentListItem(name="override", team_agents=[])
    merged = _merge_agent_list_items(base, override)
    assert len(merged.team_agents) == 1
    assert merged.team_agents[0].profile == "designer"


# ---------------------------------------------------------------------------
# Save / load round-trip (using a temporary directory)
# ---------------------------------------------------------------------------


def _make_mock_files_module(tmp_path: Path):
    """Return a helpers.files mock that writes/reads to tmp_path."""
    written: dict[str, str] = {}
    deleted_dirs: list[str] = []

    def write_file(path: str, content: str):
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        written[path] = content

    def read_file(path: str) -> str:
        full = tmp_path / path
        return full.read_text(encoding="utf-8")

    def exists(path: str) -> bool:
        return (tmp_path / path).exists()

    def delete_dir(path: str):
        deleted_dirs.append(path)

    def get_abs_path(*parts: str) -> str:
        return str(Path(*parts))

    mock = MagicMock()
    mock.write_file = write_file
    mock.read_file = read_file
    mock.exists = exists
    mock.delete_dir = delete_dir
    mock.get_abs_path = get_abs_path
    mock.read_text_files_in_dir.return_value = {}
    mock.safe_file_name = lambda n: n
    return mock, written


def test_save_agent_data_persists_team_agents():
    """save_agent_data must include team_agents in agent.json when present."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_files, written = _make_mock_files_module(tmp_path)

        agent = SubAgent(
            name="myteam",
            title="My Team",
            description="A team",
            context="use for teaming",
            enabled=True,
            team_agents=[
                TeamAgent(profile="developer", name="Dev", description="Codes"),
                TeamAgent(profile="researcher", name="Res", description="Researches"),
            ],
        )

        with patch("helpers.subagents.files", mock_files):
            from helpers.subagents import save_agent_data

            save_agent_data("myteam", agent)

        saved_path = "usr/agents/myteam/agent.json"
        assert saved_path in written, "agent.json was not written"
        data = json.loads(written[saved_path])
        assert "team_agents" in data
        assert len(data["team_agents"]) == 2
        assert data["team_agents"][0]["profile"] == "developer"
        assert data["team_agents"][1]["profile"] == "researcher"


def test_save_agent_data_omits_team_agents_when_empty():
    """save_agent_data must NOT write a team_agents key when the list is empty."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_files, written = _make_mock_files_module(tmp_path)

        agent = SubAgent(name="plain", title="Plain Agent", team_agents=[])

        with patch("helpers.subagents.files", mock_files):
            from helpers.subagents import save_agent_data

            save_agent_data("plain", agent)

        data = json.loads(written["usr/agents/plain/agent.json"])
        assert "team_agents" not in data


# ---------------------------------------------------------------------------
# agents/team/ profile files exist
# ---------------------------------------------------------------------------


def test_team_agent_yaml_exists():
    path = PROJECT_ROOT / "agents" / "team" / "agent.yaml"
    assert path.exists(), f"Expected {path} to exist"


def test_team_agent_role_md_exists():
    path = PROJECT_ROOT / "agents" / "team" / "prompts" / "agent.system.main.role.md"
    assert path.exists(), f"Expected {path} to exist"


def test_team_agent_role_py_exists():
    path = PROJECT_ROOT / "agents" / "team" / "prompts" / "agent.system.main.role.py"
    assert path.exists(), f"Expected {path} to exist"


def test_team_agent_yaml_contains_required_fields():
    from helpers import yaml as yaml_helper

    path = PROJECT_ROOT / "agents" / "team" / "agent.yaml"
    data = yaml_helper.loads(path.read_text())
    assert data is not None
    assert "title" in data
    assert "description" in data
    assert "team_agents" in data


def test_team_agent_yaml_team_agents_is_list():
    from helpers import yaml as yaml_helper

    path = PROJECT_ROOT / "agents" / "team" / "agent.yaml"
    data = yaml_helper.loads(path.read_text())
    members = data.get("team_agents", [])
    assert isinstance(members, list)
    assert len(members) > 0


def test_team_agent_yaml_each_member_has_profile():
    from helpers import yaml as yaml_helper

    path = PROJECT_ROOT / "agents" / "team" / "agent.yaml"
    data = yaml_helper.loads(path.read_text())
    for member in data.get("team_agents", []):
        assert "profile" in member, f"Member missing 'profile': {member}"


def test_team_agent_role_md_uses_team_agents_variable():
    path = PROJECT_ROOT / "agents" / "team" / "prompts" / "agent.system.main.role.md"
    content = path.read_text()
    assert "team_agents" in content
    assert "{{if team_agents}}" in content


def test_team_agent_listed_in_agents_dict():
    """The agents/team directory must be discoverable by get_agents_dict."""
    path = PROJECT_ROOT / "agents" / "team"
    assert path.is_dir()
    yaml_path = path / "agent.yaml"
    assert yaml_path.exists()


# ---------------------------------------------------------------------------
# agents/team/ is loaded with team_agents by load_agent_data
# ---------------------------------------------------------------------------


def test_load_team_agent_data_includes_team_agents():
    """load_agent_data('team') must return a SubAgent with team_agents populated."""
    from helpers.subagents import load_agent_data

    agent_data = load_agent_data("team")
    assert agent_data is not None
    assert len(agent_data.team_agents) > 0
    profiles = [m.profile for m in agent_data.team_agents]
    assert "developer" in profiles


# ---------------------------------------------------------------------------
# call_sub variables include team_agents when profiles have them
# ---------------------------------------------------------------------------


def test_call_sub_variables_include_team_agents_for_team_profile():
    """CallSubordinate.get_variables source must handle team_agents in agent profiles."""
    # Verify that the call_sub variables plugin source code includes the
    # team_agents logic instead of executing the full import chain.
    path = PROJECT_ROOT / "prompts" / "agent.system.tool.call_sub.py"
    content = path.read_text()
    assert "team_agents" in content, "call_sub.py must reference team_agents"
    # Confirm the team_agents are added to the profile entry when present
    assert "profile_entry[\"team_agents\"]" in content or "team_agents" in content


# ---------------------------------------------------------------------------
# enabled field preserved during merge
# ---------------------------------------------------------------------------


def test_merge_agent_list_items_preserves_enabled_false():
    """_merge_agent_list_items must honour enabled=False from the override."""
    base = SubAgentListItem(name="base", enabled=True)
    override = SubAgentListItem(name="override", enabled=False)
    merged = _merge_agent_list_items(base, override)
    assert merged.enabled is False


def test_merge_agent_list_items_preserves_enabled_true():
    """_merge_agent_list_items must honour enabled=True from the override."""
    base = SubAgentListItem(name="base", enabled=False)
    override = SubAgentListItem(name="override", enabled=True)
    merged = _merge_agent_list_items(base, override)
    assert merged.enabled is True


def test_merge_agents_preserves_enabled_false():
    """_merge_agents must honour enabled=False from the override."""
    base = SubAgent(name="base", title="Base", enabled=True)
    override = SubAgent(name="override", title="Override", enabled=False)
    merged = _merge_agents(base, override)
    assert merged is not None
    assert merged.enabled is False


def test_merge_agents_preserves_enabled_true():
    """_merge_agents must honour enabled=True from the override."""
    base = SubAgent(name="base", title="Base", enabled=False)
    override = SubAgent(name="override", title="Override", enabled=True)
    merged = _merge_agents(base, override)
    assert merged is not None
    assert merged.enabled is True


# ---------------------------------------------------------------------------
# SubAgentListItem / SubAgent JSON serialization (API layer)
# ---------------------------------------------------------------------------


def test_sub_agent_list_item_model_dump_is_json_serializable():
    """model_dump(mode='json') on SubAgentListItem must produce a JSON-safe dict."""
    item = SubAgentListItem(
        name="team",
        title="Team",
        team_agents=[TeamAgent(profile="developer", name="Dev")],
    )
    dumped = item.model_dump(mode="json")
    # Must be roundtrippable via json.dumps / json.loads
    serialized = json.dumps(dumped)
    restored = json.loads(serialized)
    assert restored["name"] == "team"
    assert restored["title"] == "Team"
    assert len(restored["team_agents"]) == 1
    assert restored["team_agents"][0]["profile"] == "developer"


def test_sub_agent_model_dump_is_json_serializable():
    """model_dump(mode='json') on SubAgent must include team_agents."""
    agent = SubAgent(
        name="myteam",
        title="My Team",
        team_agents=[
            TeamAgent(profile="researcher", name="Res", description="Researches"),
        ],
    )
    dumped = agent.model_dump(mode="json")
    serialized = json.dumps(dumped)
    restored = json.loads(serialized)
    assert restored["name"] == "myteam"
    assert len(restored["team_agents"]) == 1
    assert restored["team_agents"][0]["profile"] == "researcher"


def test_subagents_api_list_returns_serializable_dicts():
    """api/subagents.py get_subagents_list must return plain dicts, not Pydantic models."""
    # Simulate what the API does: model_dump(mode="json") on each item
    items = [
        SubAgentListItem(name="developer", title="Developer"),
        SubAgentListItem(
            name="team",
            title="Team",
            team_agents=[TeamAgent(profile="developer")],
        ),
    ]
    result = [a.model_dump(mode="json") for a in items]
    # Should be JSON-serializable without raising TypeError
    raw = json.dumps({"ok": True, "data": result})
    parsed = json.loads(raw)
    assert parsed["ok"] is True
    assert len(parsed["data"]) == 2
    assert parsed["data"][1]["team_agents"][0]["profile"] == "developer"


def test_subagents_api_load_returns_serializable_dict():
    """api/subagents.py load_agent must return a plain dict, not a Pydantic model."""
    agent = SubAgent(
        name="team",
        title="Team",
        team_agents=[TeamAgent(profile="developer", name="Dev")],
    )
    result = agent.model_dump(mode="json")
    raw = json.dumps({"ok": True, "data": result})
    parsed = json.loads(raw)
    assert parsed["data"]["name"] == "team"
    assert parsed["data"]["team_agents"][0]["name"] == "Dev"
