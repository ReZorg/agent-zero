"""GET+POST /api/plugins/_ecosystem/ecosystem

Returns the curated Agent Zero ecosystem catalog. The catalog is static
curated data; no external network calls are made during this request.
"""
from __future__ import annotations

from helpers.api import ApiHandler, Request, Response


class Ecosystem(ApiHandler):
    """Return the curated A0 ecosystem catalog."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip()
        if not action or action == "get_catalog":
            return self._get_catalog()
        return {"success": False, "error": f"Unknown action: {action!r}"}

    def _get_catalog(self) -> dict:
        from plugins._ecosystem.helpers.catalog import CATALOG

        return {"success": True, "catalog": CATALOG}
