# Action API authority model

The REST service is transport and orchestration around the same `DesignFlowAdapter` used by MCP. It does not recreate semantic validation.

| Operation | Operational write | Semantic authority change |
|---|---:|---:|
| Create/resume project | Yes | No decision authority |
| Import draft | Yes | No |
| Preview draft | No authoritative write | No |
| Lock round | Yes | **Yes** |
| Compile documents | No semantic write | No |
| End session | Yes | No decision authority |

Authentication permits API access; it does not constitute owner approval. `lockRound` is marked consequential in OpenAPI and must follow preview plus explicit approval.

The Action registry owns only opaque project routing metadata. It lives at `.design-flow-action-api/registry.json`, outside native project directories. The API never returns its storage keys or project-root paths.

Outward REST errors preserve stable application codes but use category-specific sanitized messages. Raw adapter, engine, and operating-system messages remain outside client responses so physical project paths and infrastructure details are not disclosed.
