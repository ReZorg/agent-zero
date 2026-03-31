"""
VariablesPlugin companion for agent.system.main.role.md (team agent).

Provides ``team_agents``, a human-readable listing of the team members
defined in the agent profile's ``team_agents`` list.

The plugin reads ``team_agents`` from the loaded ``SubAgent`` profile for the
current agent.  Each entry carries a ``profile``, an optional ``name``, and
an optional ``description``.  When no team members are defined the plugin
returns an empty string so that the ``{{if team_agents}}`` guard in the
template suppresses the section cleanly.
"""

from typing import Any, TYPE_CHECKING

from helpers.files import VariablesPlugin

if TYPE_CHECKING:
    from agent import Agent


class TeamRoleVariables(VariablesPlugin):
    """Supply ``team_agents`` variable to the team-agent role prompt."""

    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        agent: "Agent | None" = kwargs.get("_agent", None)

        team_agents_text = ""

        if agent is not None and agent.config.profile:
            try:
                from helpers import subagents

                profile_data = subagents.load_agent_data(agent.config.profile)
                members = profile_data.team_agents or []
                if members:
                    lines: list[str] = []
                    for member in members:
                        display_name = member.name or member.profile
                        line = f"- **{display_name}** (profile: `{member.profile}`)"
                        if member.description:
                            line += f": {member.description}"
                        lines.append(line)
                    team_agents_text = "\n".join(lines)
            except Exception:
                team_agents_text = ""

        return {"team_agents": team_agents_text}
