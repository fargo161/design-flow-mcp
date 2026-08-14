"""MCP tool registration for the deliberately narrow adapter surface."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .adapter import DesignFlowAdapter


REQUIRED_TOOLS = {
    "readiness",
    "new_project",
    "resume_project",
    "get_state",
    "get_unresolved",
    "get_round",
    "import_draft",
    "preview_round",
    "lock_round",
    "compile_context_handoff",
    "compile_living_document",
    "recommend_next_round",
    "end_session",
}

READ_ONLY_TOOLS = {
    "readiness",
    "get_state",
    "get_unresolved",
    "get_round",
    "preview_round",
    "compile_context_handoff",
    "compile_living_document",
    "recommend_next_round",
    "get_decision_ledger",
    "get_concepts",
    "get_trace",
    "get_session_brief",
}

MUTATING_TOOLS = {"new_project", "resume_project", "import_draft", "lock_round", "end_session"}

TOOL_ANNOTATIONS = {
    name: ToolAnnotations(
        title=name.replace("_", " ").title(),
        readOnlyHint=name in READ_ONLY_TOOLS,
        destructiveHint=name == "lock_round",
        idempotentHint=name in READ_ONLY_TOOLS,
        openWorldHint=False,
    )
    for name in READ_ONLY_TOOLS | MUTATING_TOOLS
}

TOOL_EFFECTS = {
    name: {
        "effect": (
            "authoritative-write"
            if name == "lock_round"
            else "working-state-write"
            if name in MUTATING_TOOLS
            else "read-only"
        ),
        "requiresExplicitConfirmation": name == "lock_round",
    }
    for name in READ_ONLY_TOOLS | MUTATING_TOOLS
}


def _metadata(name: str) -> dict[str, Any]:
    return {"design-flow/action": TOOL_EFFECTS[name]}


def register_tools(mcp: MCPServer, adapter: DesignFlowAdapter) -> None:
    @mcp.tool(annotations=TOOL_ANNOTATIONS["readiness"], meta=_metadata("readiness"))
    def readiness() -> dict[str, Any]:
        """Read-only. Report adapter/engine versions, root confinement, and active-project status. Changes no semantic authority."""
        return adapter.invoke(adapter.readiness)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["new_project"], meta=_metadata("new_project"))
    def new_project(
        project_name: str,
        project_path: str,
        project_id: str | None = None,
        mode: str = "DISCOVERY",
        description: str = "",
    ) -> dict[str, Any]:
        """Mutating setup operation. Create a project through the engine and start its Design Flow session. It invents no decisions and creates no decision authority."""
        return adapter.invoke(
            adapter.new_project,
            project_name=project_name,
            project_path=project_path,
            project_id=project_id,
            mode=mode,
            description=description,
        )

    @mcp.tool(annotations=TOOL_ANNOTATIONS["resume_project"], meta=_metadata("resume_project"))
    def resume_project(project_path: str) -> dict[str, Any]:
        """Mutating session operation. Validate and open an existing engine project, then resume/start its Design Flow session. It never repairs invalid persisted state."""
        return adapter.invoke(adapter.resume_project, project_path=project_path)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_state"], meta=_metadata("get_state"))
    def get_state() -> dict[str, Any]:
        """Read-only. Return concise state compiled by Design Flow. Requires an active project and cannot alter decisions, TRACE, or persistence."""
        return adapter.invoke(adapter.get_state)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_unresolved"], meta=_metadata("get_unresolved"))
    def get_unresolved() -> dict[str, Any]:
        """Read-only. Return the engine's canonical unresolved register. Requires an active project and does not reconstruct or change authority."""
        return adapter.invoke(adapter.get_unresolved)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_round"], meta=_metadata("get_round"))
    def get_round() -> dict[str, Any]:
        """Read-only. Return the active draft summary and latest committed round. Requires an active project and cannot edit either record."""
        return adapter.invoke(adapter.get_round)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["import_draft"], meta=_metadata("import_draft"))
    def import_draft(
        draft: dict[str, Any] | None = None,
        draft_file_path: str | None = None,
    ) -> dict[str, Any]:
        """Mutating working-state operation. Import exactly one structured object or allowed-root file through engine draft intake. It does not commit a decision or change semantic authority."""
        return adapter.invoke(
            adapter.import_draft, draft=draft, draft_file_path=draft_file_path
        )

    @mcp.tool(annotations=TOOL_ANNOTATIONS["preview_round"], meta=_metadata("preview_round"))
    def preview_round() -> dict[str, Any]:
        """Read-only simulation. This is non-authoritative and does not commit any decision. Requires an active draft and uses the engine preview path only."""
        return adapter.invoke(adapter.preview_round)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["lock_round"], meta=_metadata("lock_round"))
    def lock_round() -> dict[str, Any]:
        """Authority-changing operation. This commits owner-approved draft state through the Design Flow semantic engine and changes authoritative project state. Requires a complete valid draft; failures preserve it."""
        return adapter.invoke(adapter.lock_round)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["compile_context_handoff"], meta=_metadata("compile_context_handoff"))
    def compile_context_handoff() -> dict[str, Any]:
        """Read-only. Compile Context Handoff content with the engine compiler. Requires an active project and cannot rewrite semantic state."""
        return adapter.invoke(adapter.compile_context_handoff)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["compile_living_document"], meta=_metadata("compile_living_document"))
    def compile_living_document() -> dict[str, Any]:
        """Read-only. Compile the Living Application Document with the engine renderer. Requires an active project and cannot rewrite semantic state."""
        return adapter.invoke(adapter.compile_living_document)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["recommend_next_round"], meta=_metadata("recommend_next_round"))
    def recommend_next_round() -> dict[str, Any]:
        """Read-only advisory operation. Return the engine's bounded recommendation. It is non-authoritative and never starts a round."""
        return adapter.invoke(adapter.recommend_next_round)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["end_session"], meta=_metadata("end_session"))
    def end_session() -> dict[str, Any]:
        """Mutating session operation. End the active Design Flow session safely through the engine. It does not mark the project complete or commit a draft."""
        return adapter.invoke(adapter.end_session)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_decision_ledger"], meta=_metadata("get_decision_ledger"))
    def get_decision_ledger() -> dict[str, Any]:
        """Read-only. Return a concise engine decision-ledger view. It exposes no mutation capability."""
        return adapter.invoke(adapter.get_decision_ledger)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_concepts"], meta=_metadata("get_concepts"))
    def get_concepts() -> dict[str, Any]:
        """Read-only. Return concise current, affected, and historical engine concepts. It exposes no mutation capability."""
        return adapter.invoke(adapter.get_concepts)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_trace"], meta=_metadata("get_trace"))
    def get_trace() -> dict[str, Any]:
        """Read-only. Return engine-owned TRACE records. No tool can append, edit, or delete TRACE directly."""
        return adapter.invoke(adapter.get_trace)

    @mcp.tool(annotations=TOOL_ANNOTATIONS["get_session_brief"], meta=_metadata("get_session_brief"))
    def get_session_brief() -> dict[str, Any]:
        """Read-only. Return the engine session brief and semantic session identity. It does not conflate the MCP connection with the Design Flow session."""
        return adapter.invoke(adapter.get_session_brief)
