# Phase 2 owner decisions

## Status: NOT READY for hosted deployment or public submission

Phase 1 intentionally stops before the following decisions and implementation work.

| Decision | Why owner input is required |
|---|---|
| Hosting provider, domain, region, and operating model | Determines the public HTTPS MCP endpoint, runtime controls, availability, and cost. |
| OAuth 2.1 authorization provider and account lifecycle | Customer data and writes cannot use anonymous shared access. |
| Tenant identity, project namespace, storage backend, and migration policy | The current process-global adapter and filesystem paths are single-user/local only. |
| Hosted tool contract | `project_path` and `draft_file_path` must not expose server filesystem semantics. |
| Retention, deletion, backup, recovery, and audit policy | These define the actual public data-handling commitments. |
| Privacy policy, terms, public support URL, and publisher identity | Required legal and operational statements cannot be invented by implementation. |
| Public submission timing, countries, test credentials, and reviewer access | These are distribution choices and require separate authorization. |

No hosting, OAuth, Tenant storage, public submission, or app-directory registration has been implemented. Phase 2 must begin only after explicit owner direction.
