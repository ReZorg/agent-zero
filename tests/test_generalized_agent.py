"""
Tests for helpers/files.py – replace_placeholders_text expression evaluation.

Covers:
- Backward-compatible simple {{key}} replacement
- Nested dict access  {{d["k1"]["k2"]}}
- List index access   {{lst[0]}}
- Unknown expressions left untouched
- Generalized-agent role_config pattern
- Agents directory contains the generalized agent profile
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.files import replace_placeholders_text


# ---------------------------------------------------------------------------
# replace_placeholders_text – simple (backward-compatible) cases
# ---------------------------------------------------------------------------


def test_simple_key_replacement():
    result = replace_placeholders_text("Hello {{name}}!", name="World")
    assert result == "Hello World!"


def test_multiple_simple_keys():
    result = replace_placeholders_text(
        "{{greeting}} {{target}}!", greeting="Hello", target="World"
    )
    assert result == "Hello World!"


def test_simple_key_missing_leaves_placeholder():
    result = replace_placeholders_text("Hello {{missing}}!")
    assert "{{missing}}" in result


# ---------------------------------------------------------------------------
# replace_placeholders_text – expression / nested-dict cases
# ---------------------------------------------------------------------------


def test_nested_dict_string_key_access():
    """{{d["key"]}} should resolve to the value at d["key"]."""
    d = {"title": "My Title"}
    result = replace_placeholders_text('{{d["title"]}}', d=d)
    assert result == "My Title"


def test_deeply_nested_dict_access():
    """{{cfg["a"]["b"]["c"]}} should traverse three levels."""
    cfg = {"a": {"b": {"c": "deep_value"}}}
    result = replace_placeholders_text('{{cfg["a"]["b"]["c"]}}', cfg=cfg)
    assert result == "deep_value"


def test_list_index_access():
    """{{lst[0]}} should return the first element."""
    lst = ["alpha", "beta", "gamma"]
    result = replace_placeholders_text("{{lst[0]}}", lst=lst)
    assert result == "alpha"


def test_unknown_expression_is_left_intact():
    """A placeholder that cannot be evaluated should remain unchanged."""
    result = replace_placeholders_text("{{undefined_var}}")
    assert "{{undefined_var}}" in result


def test_include_directive_is_left_intact():
    """{{ include 'file.md' }} must survive replace_placeholders_text unchanged."""
    template = "before {{ include 'file.md' }} after"
    result = replace_placeholders_text(template)
    assert "{{ include 'file.md' }}" in result


# ---------------------------------------------------------------------------
# role_config pattern (generalized agent use-case)
# ---------------------------------------------------------------------------


def test_role_config_identity_title():
    role_config = {
        "identity": {
            "title": "Data Engineer",
            "domain": "Data Engineering",
            "mission": "Build reliable data pipelines",
        },
        "capabilities": {},
        "constraints": {},
    }
    template = '{{role_config["identity"]["title"]}}'
    result = replace_placeholders_text(template, role_config=role_config)
    assert result == "Data Engineer"


def test_role_config_identity_domain():
    role_config = {
        "identity": {
            "title": "Data Engineer",
            "domain": "Data Engineering",
            "mission": "Build reliable data pipelines",
        }
    }
    template = '{{role_config["identity"]["domain"]}}'
    result = replace_placeholders_text(template, role_config=role_config)
    assert result == "Data Engineering"


def test_role_config_empty_dict_is_falsy():
    """An empty role_config should evaluate as falsy in conditions."""
    from helpers.files import evaluate_text_conditions

    template = "{{if role_config}}CONFIGURED{{endif}}"
    result = evaluate_text_conditions(template, role_config={})
    assert "CONFIGURED" not in result


def test_role_config_populated_dict_is_truthy():
    """A non-empty role_config should cause the {{if}} block to render."""
    from helpers.files import evaluate_text_conditions

    template = "{{if role_config}}CONFIGURED{{endif}}"
    result = evaluate_text_conditions(template, role_config={"identity": {}})
    assert "CONFIGURED" in result


# ---------------------------------------------------------------------------
# Generalized agent profile files exist in agents/
# ---------------------------------------------------------------------------


def test_generalized_agent_yaml_exists():
    path = PROJECT_ROOT / "agents" / "generalized" / "agent.yaml"
    assert path.exists(), f"Expected {path} to exist"


def test_generalized_agent_role_md_exists():
    path = (
        PROJECT_ROOT
        / "agents"
        / "generalized"
        / "prompts"
        / "agent.system.main.role.md"
    )
    assert path.exists(), f"Expected {path} to exist"


def test_generalized_agent_role_py_exists():
    path = (
        PROJECT_ROOT
        / "agents"
        / "generalized"
        / "prompts"
        / "agent.system.main.role.py"
    )
    assert path.exists(), f"Expected {path} to exist"


def test_generalized_agent_communication_md_exists():
    path = (
        PROJECT_ROOT
        / "agents"
        / "generalized"
        / "prompts"
        / "agent.system.main.communication.md"
    )
    assert path.exists(), f"Expected {path} to exist"


def test_generalized_agent_yaml_contains_required_fields():
    """The agent.yaml must have title, description and context keys."""
    from helpers import yaml as yaml_helper

    path = PROJECT_ROOT / "agents" / "generalized" / "agent.yaml"
    data = yaml_helper.loads(path.read_text())
    assert data is not None
    assert "title" in data
    assert "description" in data
    assert "context" in data


def test_generalized_agent_listed_in_agents_dict():
    """The agents/generalized directory must exist so the agent is discoverable."""
    path = PROJECT_ROOT / "agents" / "generalized"
    assert path.is_dir(), (
        f"Expected agents/generalized directory to exist at {path}"
    )
    yaml_path = path / "agent.yaml"
    assert yaml_path.exists(), "Expected agents/generalized/agent.yaml to exist"


def test_generalized_agent_role_md_uses_dynamic_variables():
    """The role.md must reference role_config dynamic variables."""
    path = (
        PROJECT_ROOT
        / "agents"
        / "generalized"
        / "prompts"
        / "agent.system.main.role.md"
    )
    content = path.read_text()
    assert "role_config" in content
    assert "{{if role_config}}" in content
