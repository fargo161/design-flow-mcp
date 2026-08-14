# Local Action API development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
$env:DESIGN_FLOW_PROJECT_ROOT="$HOME\Documents\DesignFlowProjects"
$env:DESIGN_FLOW_API_KEY="replace-with-at-least-32-random-characters"
.\.venv\Scripts\python.exe -m design_flow_action_api
```

Open `http://127.0.0.1:8080/docs`. Every API operation, including health, requires the `X-API-Key` header.

Export and validate the exact schema:

```powershell
.\.venv\Scripts\python.exe -m design_flow_action_api --export-openapi openapi.json
.\.venv\Scripts\python.exe scripts\validate_action_openapi.py openapi.json
```

Keys shorter than 32 characters are rejected during configuration. Do not commit `.env` files or real keys, place secrets in project files, or include them in a Docker build context. Local HTTP is for development only; a Custom GPT requires a hosted HTTPS endpoint.
