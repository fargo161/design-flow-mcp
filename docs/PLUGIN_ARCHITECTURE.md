# Private plugin architecture

Phase 1 packages the existing Python MCP adapter as a local, private-testable plugin. It does not introduce another semantic layer.

```text
Codex or compatible private MCP host
  -> chatgpt/plugin/design-flow
  -> local stdio command: design-flow-mcp
  -> DesignFlowAdapter
  -> design-flow-system 0.2.0
  -> one confined local project root
```

The manifest supplies plugin identity, starter prompts, assets, the workflow skill, and the MCP server registration. The MCP server remains the source of tool schemas and annotations. No optional UI or JavaScript package is required for Phase 1.

## Action model

- Read-only tools declare `readOnlyHint=true`, `destructiveHint=false`, and `openWorldHint=false`.
- Working/session tools declare `readOnlyHint=false` and do not claim semantic authority.
- `lock_round` declares a destructive authoritative write and namespaced metadata requiring explicit confirmation.
- The workflow skill forbids automatic locking and separates recommendation, owner decision, preview, and commit.

MCP annotations are client hints, not authorization. The engine lock remains the actual authority boundary.

## Scope boundary

This package inherits `DESIGN_FLOW_PROJECT_ROOT`, runs locally, and supports one active project/session per server process. It contains no hosted endpoint, authentication, tenant storage, public listing, or submission configuration.
