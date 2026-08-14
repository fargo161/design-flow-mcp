---
name: design-flow-workflow
description: Guide safe use of the Design Flow MCP tools for persistent design projects, including project inspection, draft import, non-authoritative preview, explicit owner-approved locking, unresolved tracking, provenance review, and document compilation. Use when a user asks to create, resume, inspect, advance, preview, lock, or compile a Design Flow project.
---

# Design Flow Workflow

Preserve the engine-owned authority boundary throughout every design round.

## Required sequence

1. Call `readiness` before project work.
2. Call `new_project` or `resume_project` only with a path below the configured project root.
3. Inspect `get_state`, `get_unresolved`, and `get_round` before proposing changes.
4. Keep recommendations advisory and owner answers explicit.
5. Import a bounded structured draft with `import_draft`.
6. Call `preview_round` and clearly label the result non-authoritative.
7. Present the preview and wait for explicit owner approval.
8. Call `lock_round` only after the user expressly confirms the currently reviewed draft.
9. Compile the context handoff or living document after a successful lock.
10. Use `recommend_next_round` as advice only; never start or lock it automatically.

## Authority rules

- Treat `RECOMMENDATION != OWNER DECISION`.
- Treat `DRAFT PREVIEW != COMMIT`.
- Never infer approval from praise, silence, or acceptance of a recommendation.
- Never invoke `lock_round` in the same step that first presents a preview.
- State that `lock_round` changes authoritative project state through validated engine APIs.
- Do not claim `end_session` completes the project or commits a draft.

## Safety boundaries

Do not request or simulate raw persistence edits, TRACE edits, decision rewrites, shell access, filesystem browsing, Python evaluation, forced supersession, or manifest mutation. If a requested outcome requires one of these, explain that the plugin intentionally does not expose it.

This package is private/local Phase 1 software. Do not imply that hosted deployment, authentication, tenant isolation, or public distribution exists.
