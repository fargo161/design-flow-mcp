# ChatGPT setup

This guide intentionally avoids fixed UI labels because ChatGPT custom-app and developer-mode screens can vary by plan and product version.

## 1. Run the server

Install the project and set `DESIGN_FLOW_PROJECT_ROOT` as shown in the README. Use `stdio` for a local MCP host that can launch subprocesses, or Streamable HTTP for a remotely reachable deployment.

## 2. Make it reachable

For local development, register the command that runs:

```text
python -m design_flow_mcp.server
```

For a remote client, deploy Streamable HTTP behind HTTPS and appropriate authentication. Do not expose the local development listener directly to the internet. This repository does not include a tunnel.

## 3. Register the custom MCP app

Add the command or HTTPS MCP endpoint in ChatGPT where custom MCP apps are supported.

> ChatGPT's exact custom-app/developer-mode UI may differ by plan and product version; follow the current OpenAI custom MCP app instructions when registering the server.

## 4. Enable it in a conversation

Enable or select the registered Design Flow app for the conversation. The MCP connection is not the Design Flow semantic session; `new_project` or `resume_project` creates/resumes that engine-owned session.

## 5. Test read-only behavior first

Call `readiness`. Then create or resume a project and call `get_state` and `get_unresolved`. Confirm the returned allowed root and engine version are expected.

## 6. Test a draft preview

Call `import_draft` with a strict Design Flow draft object, then `preview_round`. Confirm the response says:

```json
{"authoritative": false, "status": "DRAFT_PREVIEW"}
```

Import and preview do not create committed decisions.

## 7. Test locking last

Only call `lock_round` after the owner has explicitly approved the complete draft. This tool changes authoritative project state through the engine. Validation failures retain the draft and return a structured error.

