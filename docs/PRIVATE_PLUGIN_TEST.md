# Private plugin test

## Prerequisites

Install the adapter in the Python environment visible to the plugin host:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
$env:DESIGN_FLOW_PROJECT_ROOT="$HOME\Documents\DesignFlowProjects"
New-Item -ItemType Directory -Force $env:DESIGN_FLOW_PROJECT_ROOT | Out-Null
```

The packaged `.mcp.json` launches `design-flow-mcp` over local stdio and inherits the project-root environment variable. This is a local/private route, not a ChatGPT remote custom-app connection.

## Acceptance flow

1. Load `chatgpt/plugin/design-flow` in a private plugin-capable host.
2. Call `readiness` and verify adapter `0.1.0`, engine `0.2.0`, and the expected local root.
3. Create or resume a project below that root.
4. Inspect state and unresolved work.
5. Import a structured draft and preview it.
6. Verify the preview is labeled non-authoritative and does not change the decision ledger.
7. Ask for explicit owner approval. Do not combine first preview and lock in one action.
8. After approval, invoke `lock_round` and verify the authoritative history.
9. Compile the context handoff and living document.
10. End and resume the session, then verify the committed decision remains.

Run repository validation with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\validate_phase1_package.py
```

Local Streamable HTTP may still be tested at `http://127.0.0.1:8000/mcp`, but it is not an installable remote ChatGPT endpoint and must not be publicly exposed.
