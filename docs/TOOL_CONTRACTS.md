# Tool contracts

All responses use either `{"ok": true, "result": ...}` or `{"ok": false, "error": {"code": ..., "message": ...}}`.

| Tool | Mode | Preconditions | Boundary |
|---|---|---|---|
| `readiness` | Read-only | None | Reports safe status only. |
| `new_project` | Setup mutation | Path inside allowed root | Creates through engine; no decisions. |
| `resume_project` | Session mutation | Valid project inside allowed root | Activation fails closed; no repair. |
| `get_state` | Read-only | Active project | Uses engine state compiler. |
| `get_unresolved` | Read-only | Active project | Uses canonical unresolved compiler. |
| `get_round` | Read-only | Active project | Concise draft/committed summaries only. |
| `import_draft` | Working-state mutation | Active engine session | Does not commit or change decision authority. |
| `preview_round` | Read-only simulation | Active draft | Non-authoritative; does not commit any decision. |
| `lock_round` | Authority-changing | Complete, owner-approved valid draft | Commits only through engine lock; failure preserves draft. |
| `compile_context_handoff` | Read-only | Active project | Uses engine compiler. |
| `compile_living_document` | Read-only | Active project | Uses engine renderer. |
| `recommend_next_round` | Read-only advisory | Active project | Does not launch a round. |
| `end_session` | Session mutation | Active Design Flow session | Does not commit the draft or complete the project. |
| `get_decision_ledger` | Read-only | Active project | No ledger mutation. |
| `get_concepts` | Read-only | Active project | No concept mutation. |
| `get_trace` | Read-only | Active project | No TRACE mutation. |
| `get_session_brief` | Read-only | Active project | Reports engine semantic session ID. |

## Error codes

`PROJECT_NOT_FOUND`, `PROJECT_VALIDATION_FAILED`, `NO_ACTIVE_PROJECT`, `NO_ACTIVE_DRAFT`, `DRAFT_VALIDATION_FAILED`, `ROUND_LOCK_FAILED`, `ENGINE_INTEGRITY_ERROR`, `PATH_OUTSIDE_ALLOWED_ROOT`, and `UNSUPPORTED_OPERATION` are reserved stable categories. Safe engine detail is retained in the message; persisted state is never automatically repaired.

