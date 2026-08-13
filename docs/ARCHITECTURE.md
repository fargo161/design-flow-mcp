# Architecture

```text
ChatGPT / MCP client
        |
        v
MCP Python SDK transport
        |
        v
DesignFlowAdapter (path checks, error mapping, one active project)
        |
        v
design-flow-system 0.2.0 public APIs
        |
        v
PersistentProject / Session / Draft / TRACE / Compilers / ProjectStore
        |
        v
project directory below DESIGN_FLOW_PROJECT_ROOT
```

The adapter owns transport state, root confinement, concise serialization, and stable error categories. It does not own semantic logic.

## Runtime model

One MCP server process holds at most one active `PersistentProject`. The configured root may contain many projects, but switching projects requires `new_project` or `resume_project`. MCP client connection identity, Design Flow session identity, and project identity are separate. The Design Flow session ID always comes from the engine.

## Engine dependency

`pyproject.toml` pins `design-flow-system` to merge commit `30bedf2032179fcb46186f30cc86c33b070c17d1` (version `0.2.0`). No upstream source is copied, patched, or imported through a submodule.

## Semantic writes

- New/resume/end operations call `PersistentProject` lifecycle APIs.
- Structured draft objects are serialized to a short-lived intake file inside the active project, then passed to the public `PersistentProject.import_draft()` API. The file is removed immediately.
- Preview calls `PersistentProject.preview_draft()` and does not mutate the authoritative workspace.
- Lock calls `PersistentProject.lock_draft()`, the engine's validated all-or-nothing commit point.
- Compilers and read views call engine APIs; they do not reconstruct semantic truth.

There are no raw mutation, shell, arbitrary filesystem, Python evaluation, Git, environment-dump, or credential tools.

## Transport

The adapter uses the official MCP Python SDK v2. Local `stdio` is the default. Streamable HTTP is supported for deployment, but TLS, authentication, process management, public host/origin allowlists, and network ingress remain deployment responsibilities.

