"""
VariablesPlugin companion for agent.system.main.role.md (generalized agent).

Provides `role_config`, a nested variable structure of the form::

    role_config: dict[str, dict[str, Any]]
        identity: dict[str, str]
            title:   str  – display name for the current role
            domain:  str  – primary subject domain
            mission: str  – one-line purpose statement
        capabilities: dict[str, dict[str, str]]
            <name>: dict[str, str]
                title:       str
                description: str
        constraints: dict[str, str]
            <name>: str

The plugin reads the optional "role_config" entry that a superior agent may
have stored on the subordinate via ``agent.set_data("role_config", {...})``.
When no data is present the plugin returns an empty dict so that the
``{{if role_config}}`` guard in the template suppresses the section cleanly.
"""

from typing import Any, TYPE_CHECKING

from helpers.files import VariablesPlugin

if TYPE_CHECKING:
    from agent import Agent


class GeneralizedRoleVariables(VariablesPlugin):
    """Supply nested ``role_config`` variables to the generalized-agent prompt."""

    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        agent: "Agent | None" = kwargs.get("_agent", None)

        # A superior agent can pre-populate role_config on the subordinate with
        #   sub.set_data("role_config", { "identity": {...}, "capabilities": {...}, ... })
        # When no data exists we return an empty dict so the template guard
        # {{if role_config}} evaluates to False and the section is omitted.
        role_config: dict[str, Any] = {}
        if agent is not None:
            stored_role_config: Any = agent.get_data("role_config")
            if isinstance(stored_role_config, dict):
                role_config = stored_role_config

        return {"role_config": role_config}
