# Phase 1 data handling draft

The local private package persists Design Flow project data under the operator-selected `DESIGN_FLOW_PROJECT_ROOT`. Stored data can include projects, rounds, questions, recommendations, owner answers, decisions, concepts, unresolved items, TRACE/provenance, generated documents, and session metadata.

The adapter does not send this data to a hosted Design Flow service. The MCP client or model provider may process tool inputs and outputs under that provider's own policies; Phase 1 makes no independent claim about those systems.

Retention lasts until the local operator deletes or archives the project directory. Deletion is a local operator action and is intentionally not exposed as an MCP tool. Backups and recovery remain the operator's responsibility.

This is a development draft, not a published privacy policy. Public privacy, retention, deletion-request, support, and legal terms require Phase 2 owner decisions.
