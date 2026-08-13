# Design Flow MCP

A thin MCP bridge between ChatGPT-compatible MCP clients and Design Flow System v0.2.

The adapter exposes a small capability-based tool surface while all decisions, provenance, TRACE, validation, persistence, and commit boundaries remain inside the Design Flow engine.

## What this is

- A transport and orchestration layer around `design-flow-system`.
- Adapter version `0.1.0`.
- Engine version `0.2.0`, pinned to merge commit `30bedf2032179fcb46186f30cc86c33b070c17d1`.
- One active Design Flow project/session per server process; multiple project paths may exist below the configured root.

## What it is not

- Not the Design Flow semantic engine.
- Not an LLM provider.
- Not a database.
- Not a replacement for the Design Flow CLI.
- Not a shell, filesystem browser, Python evaluator, or raw-state editor.

## Authority boundary

`import_draft` changes working draft state but creates no decision authority. `preview_round` is explicitly non-authoritative. Only `lock_round` can change decision authority, and it calls `PersistentProject.lock_draft()` rather than editing persistence files. No tool directly edits decisions, concepts, supersession, TRACE, manifests, hashes, or project JSON.

## Tools

Read-only tools:

`readiness`, `get_state`, `get_unresolved`, `get_round`, `preview_round`, `compile_context_handoff`, `compile_living_document`, `recommend_next_round`, `get_decision_ledger`, `get_concepts`, `get_trace`, and `get_session_brief`.

Working/session or authority-changing tools:

- `new_project` and `resume_project` create or open a project and engine session.
- `import_draft` changes non-authoritative working state.
- `lock_round` is the only decision-authority-changing tool.
- `end_session` ends the Design Flow session without marking the project complete.

See [Tool contracts](docs/TOOL_CONTRACTS.md) for preconditions and exact boundaries.

## Project-root security

Set `DESIGN_FLOW_PROJECT_ROOT` to the only directory projects may occupy. Relative paths are resolved below it. Parent traversal, absolute escapes, and detectable symlink escapes are rejected. Draft file imports are subject to the same confinement.

## Local setup on Windows PowerShell

```powershell
cd $HOME\Documents
git clone https://github.com/fargo161/design-flow-mcp.git
cd design-flow-mcp

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

$env:DESIGN_FLOW_PROJECT_ROOT="$HOME\Documents\DesignFlowProjects"
New-Item -ItemType Directory -Force $env:DESIGN_FLOW_PROJECT_ROOT | Out-Null

.\.venv\Scripts\python.exe -m design_flow_mcp.server
```

The default transport is local `stdio`, where the MCP client launches this command as a subprocess.

For local Streamable HTTP development:

```powershell
.\.venv\Scripts\python.exe -m design_flow_mcp.server --transport streamable-http --host 127.0.0.1 --port 8000
```

The MCP endpoint is `http://127.0.0.1:8000/mcp`. Streamable HTTP is a deployment surface, not an authentication or tunneling solution. Do not expose it publicly without HTTPS, authentication, network policy, and the MCP SDK's production host/origin configuration.

## Development

For an editable local engine checkout, install it first and install this adapter without resolving dependencies:

```powershell
python -m pip install -e ..\design-flow-system
python -m pip install "mcp>=2,<3" build
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
python -m build
```

Normal installation uses the exact Git dependency declared in `pyproject.toml`; engine source is not copied or vendored here.

## Documents

- [Architecture](docs/ARCHITECTURE.md)
- [ChatGPT setup](docs/CHATGPT_SETUP.md)
- [Tool contracts](docs/TOOL_CONTRACTS.md)

