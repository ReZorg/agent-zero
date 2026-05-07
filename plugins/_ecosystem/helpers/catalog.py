"""Curated catalog of official agent0ai ecosystem repositories.

Each entry describes one official repo with typed metadata and a list of
in-app actions. Actions route to existing Agent Zero flows (Plugin Hub,
MCP settings, self-update) or open external URLs and copy commands.

Action types
------------
open_url     : open action.url in a new browser tab
copy_text    : copy action.text to the clipboard (toast on success)
open_plugin_hub : open the Plugin Hub browse tab
open_settings   : open Settings modal, then navigate to action.tab
"""
from __future__ import annotations

from typing import Any

# Known settings tab IDs — matches TAB_ITEMS in webui/components/settings/settings-store.js.
# Referenced by actions of type "open_settings" in CATALOG and validated by the test suite.
VALID_SETTINGS_TABS: frozenset[str] = frozenset(
    {"agent", "skills", "external", "mcp", "developer", "backup"}
)

CATALOG: list[dict[str, Any]] = [
    {
        "id": "agent-zero",
        "type": "product",
        "title": "Agent Zero",
        "subtitle": "Core AI Framework",
        "description": (
            "The open agent platform. Runs a full Linux system inside Docker, "
            "supports multi-agent cooperation, plugins, MCP, computer use, and "
            "a full-featured Web UI. This is the repo you are running right now."
        ),
        "github": "https://github.com/agent0ai/agent-zero",
        "tags": ["core", "framework"],
        "actions": [
            {
                "type": "open_settings",
                "label": "Check for Updates",
                "tab": "backup",
            },
            {
                "type": "open_url",
                "label": "Documentation",
                "url": "https://github.com/agent0ai/agent-zero/tree/main/docs",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/agent-zero",
            },
        ],
    },
    {
        "id": "a0-plugins",
        "type": "integration",
        "title": "A0 Plugins",
        "subtitle": "Community Plugin Index",
        "description": (
            "The official community plugin index. Browse, install, and contribute "
            "plugins for Agent Zero through the built-in Plugin Hub. "
            "39 open pull requests mean the community is actively growing."
        ),
        "github": "https://github.com/agent0ai/a0-plugins",
        "tags": ["plugins", "community"],
        "actions": [
            {
                "type": "open_plugin_hub",
                "label": "Browse Plugin Hub",
            },
            {
                "type": "open_url",
                "label": "Contribute a Plugin",
                "url": "https://github.com/agent0ai/a0-plugins",
            },
        ],
    },
    {
        "id": "a0-connector",
        "type": "integration",
        "title": "A0 CLI Connector",
        "subtitle": "Host Machine Integration",
        "description": (
            "Connect Agent Zero (running in Docker) to your real local files and "
            "terminal. Install A0 CLI on the host machine, run `a0`, and Agent Zero "
            "gains `text_editor_remote`, `code_execution_remote`, and "
            "`computer_use_remote` tools that act on your host."
        ),
        "github": "https://github.com/agent0ai/a0-connector",
        "tags": ["cli", "connector", "integration"],
        "actions": [
            {
                "type": "copy_text",
                "label": "Install (macOS/Linux)",
                "text": "curl -LsSf https://cli.agent-zero.ai/install.sh | sh",
            },
            {
                "type": "copy_text",
                "label": "Install (Windows)",
                "text": "irm https://cli.agent-zero.ai/install.ps1 | iex",
            },
            {
                "type": "open_url",
                "label": "CLI Connector Guide",
                "url": "https://github.com/agent0ai/agent-zero/blob/main/docs/guides/a0-cli-connector.md",
            },
        ],
    },
    {
        "id": "code-execution-mcp",
        "type": "integration",
        "title": "Code Execution MCP",
        "subtitle": "MCP Server",
        "description": (
            "Agent Zero's code execution tool exposed as a standalone MCP server. "
            "Lets other AI applications (Claude Desktop, Cursor, etc.) use the same "
            "sandboxed code execution that Agent Zero uses internally."
        ),
        "github": "https://github.com/agent0ai/code-execution-mcp",
        "tags": ["mcp", "tools", "integration"],
        "actions": [
            {
                "type": "open_settings",
                "label": "Open MCP Settings",
                "tab": "mcp",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/code-execution-mcp",
            },
        ],
    },
    {
        "id": "a0-example-plugin",
        "type": "template",
        "title": "Example Plugin",
        "subtitle": "Plugin Starter Template",
        "description": (
            "The official starter template for Agent Zero plugins. "
            "Fork or use it as a GitHub template, follow the conventions, "
            "then submit a PR to a0-plugins to list it in the Plugin Hub."
        ),
        "github": "https://github.com/agent0ai/a0-example-plugin",
        "tags": ["plugins", "template", "development"],
        "actions": [
            {
                "type": "open_url",
                "label": "Use as Template",
                "url": "https://github.com/agent0ai/a0-example-plugin/generate",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/a0-example-plugin",
            },
        ],
    },
    {
        "id": "a0-install",
        "type": "install",
        "title": "A0 Install Scripts",
        "subtitle": "Installation & Setup",
        "description": (
            "One-command installation scripts for Agent Zero. "
            "Handles Docker detection, image pull, and container setup automatically "
            "on macOS, Linux, and Windows."
        ),
        "github": "https://github.com/agent0ai/a0-install",
        "tags": ["install", "setup"],
        "actions": [
            {
                "type": "copy_text",
                "label": "Install (macOS/Linux)",
                "text": "curl -fsSL https://bash.agent-zero.ai | bash",
            },
            {
                "type": "copy_text",
                "label": "Install (Windows)",
                "text": "irm https://ps.agent-zero.ai | iex",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/a0-install",
            },
        ],
    },
    {
        "id": "a0-launcher",
        "type": "product",
        "title": "A0 Launcher",
        "subtitle": "Desktop Launcher App",
        "description": (
            "Native desktop launcher for Agent Zero. "
            "Start, stop, and manage your Agent Zero Docker instance "
            "from a lightweight desktop application without needing a terminal."
        ),
        "github": "https://github.com/agent0ai/a0-launcher",
        "tags": ["launcher", "desktop"],
        "actions": [
            {
                "type": "open_url",
                "label": "Download",
                "url": "https://github.com/agent0ai/a0-launcher/releases",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/a0-launcher",
            },
        ],
    },
    {
        "id": "space-agent",
        "type": "product",
        "title": "Space Agent",
        "subtitle": "Agent-Shaped Workspace",
        "description": (
            "The agent that re-shapes the Space. A polished, production-ready "
            "agent workspace for personal, team, desktop, and self-hosted use — "
            "built on the Agent Zero engine."
        ),
        "github": "https://github.com/agent0ai/space-agent",
        "tags": ["product", "workspace"],
        "actions": [
            {
                "type": "open_url",
                "label": "Visit space-agent.ai",
                "url": "https://space-agent.ai/",
            },
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/space-agent",
            },
        ],
    },
    {
        "id": "a0-benchmarks",
        "type": "benchmark",
        "title": "A0 Benchmarks",
        "subtitle": "LLM Benchmarking",
        "description": (
            "Benchmarking suite for evaluating LLM performance in Agent Zero workflows. "
            "Developer-facing reference for measuring and comparing model quality across "
            "agent tasks."
        ),
        "github": "https://github.com/agent0ai/a0-benchmarks",
        "tags": ["benchmarks", "development", "llm"],
        "actions": [
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/a0-benchmarks",
            },
        ],
    },
    {
        "id": "heroku-python-minimal",
        "type": "example",
        "title": "Heroku Python Minimal",
        "subtitle": "Cloud Deployment Template",
        "description": (
            "Minimal reference setup for deploying a Python application on Heroku. "
            "Starting point for cloud-hosted Agent Zero integrations or "
            "companion services."
        ),
        "github": "https://github.com/agent0ai/heroku-python-minimal",
        "tags": ["deployment", "heroku", "template"],
        "actions": [
            {
                "type": "open_url",
                "label": "GitHub",
                "url": "https://github.com/agent0ai/heroku-python-minimal",
            },
        ],
    },
]
