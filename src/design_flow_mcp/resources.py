"""Stable, read-only MCP resources derived from engine compilers."""

from __future__ import annotations

import json

from mcp.server import MCPServer

from .adapter import DesignFlowAdapter


def register_resources(mcp: MCPServer, adapter: DesignFlowAdapter) -> None:
    @mcp.resource("designflow://active/state")
    def active_state() -> str:
        """Current Design Flow state compiled by the engine."""
        return json.dumps(adapter.invoke(adapter.get_state), indent=2)

    @mcp.resource("designflow://active/unresolved")
    def active_unresolved() -> str:
        """Canonical unresolved register compiled by the engine."""
        return json.dumps(adapter.invoke(adapter.get_unresolved), indent=2)

    @mcp.resource("designflow://active/context-handoff")
    def active_context_handoff() -> str:
        """Context Handoff compiled by the engine."""
        response = adapter.invoke(adapter.compile_context_handoff)
        if not response["ok"]:
            return json.dumps(response, indent=2)
        return response["result"]["content"]

