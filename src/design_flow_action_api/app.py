from __future__ import annotations

import hmac
import logging
import time
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

from design_flow_mcp.errors import AdapterError

from . import __version__
from .config import ActionAPIConfig
from .service import ActionService


LOGGER = logging.getLogger("design_flow_action_api")
API_KEY = APIKeyHeader(name="X-API-Key", auto_error=False)


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=200)
    mode: str = "DISCOVERY"
    description: str = Field(default="", max_length=2000)


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    draft: dict[str, Any]


class SuccessResponse(BaseModel):
    ok: Literal[True] = True
    result: dict[str, Any]


ERROR_RESPONSES = {
    401: {"description": "Missing or invalid private API key"},
    404: {"description": "Project or round not found"},
    409: {"description": "Invalid project or draft lifecycle state"},
    422: {"description": "Request or Design Flow validation failed"},
}

SAFE_ERROR_MESSAGES = {
    "AUTHENTICATION_REQUIRED": "Missing or invalid API key.",
    "PROJECT_NOT_FOUND": "The requested project was not found.",
    "ROUND_NOT_FOUND": "The requested round was not found.",
    "NO_ACTIVE_PROJECT": "No project is active.",
    "NO_ACTIVE_DRAFT": "No active draft exists for this project.",
    "ROUND_LOCK_FAILED": "The draft could not be committed; it remains available for review.",
    "DRAFT_VALIDATION_FAILED": "The draft failed validation.",
    "PROJECT_VALIDATION_FAILED": "The project failed integrity validation.",
    "PATH_OUTSIDE_ALLOWED_ROOT": "The requested project reference is invalid.",
    "ENGINE_INTEGRITY_ERROR": "The Design Flow operation failed safely.",
    "UNSUPPORTED_OPERATION": "The requested operation is not supported.",
}


def create_app(config: ActionAPIConfig | None = None) -> FastAPI:
    settings = config or ActionAPIConfig.from_env()
    service = ActionService(settings.project_root)
    async def authenticate(api_key: Annotated[str | None, Depends(API_KEY)]) -> None:
        if api_key is None or not hmac.compare_digest(api_key, settings.api_key):
            LOGGER.warning("authentication_failed")
            raise AdapterError("AUTHENTICATION_REQUIRED", "Missing or invalid API key")

    app = FastAPI(
        title="Design Flow Action API",
        version=__version__,
        description=(
            "Private single-user REST adapter for Design Flow. Recommendations and previews are "
            "non-authoritative; only an explicitly approved lock commits semantic authority."
        ),
        servers=[{"url": settings.public_base_url}],
        dependencies=[Depends(authenticate)],
    )
    app.state.config = settings
    app.state.service = service

    @app.middleware("http")
    async def operational_logging(request: Request, call_next: Any) -> Any:
        started = time.perf_counter()
        response = await call_next(request)
        LOGGER.info(
            "request_complete route=%s status=%s latency_ms=%.2f",
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    @app.exception_handler(AdapterError)
    async def adapter_error_handler(_request: Request, error: AdapterError) -> JSONResponse:
        status = _status_for(error.code)
        message = SAFE_ERROR_MESSAGES.get(error.code, "The Design Flow operation failed safely.")
        LOGGER.warning("action_error code=%s status=%s", error.code, status)
        return JSONResponse(
            status_code=status,
            content={"error": {"code": error.code, "message": message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "REQUEST_VALIDATION_FAILED", "message": str(error)}},
        )

    @app.get("/health", operation_id="health", include_in_schema=False)
    def health() -> dict[str, Any]:
        return {"status": "ready", "api_version": __version__}

    @app.post("/projects", operation_id="createProject", summary="Create a Design Flow project", responses=ERROR_RESPONSES)
    def create_project(body: CreateProjectRequest) -> SuccessResponse:
        return {"ok": True, "result": service.create_project(**body.model_dump())}

    @app.get("/projects", operation_id="listProjects", summary="List private Design Flow projects", responses=ERROR_RESPONSES)
    def list_projects() -> SuccessResponse:
        return {"ok": True, "result": service.list_projects()}

    @app.post("/projects/{project_id}/resume", operation_id="resumeProject", summary="Resume a project session", responses=ERROR_RESPONSES)
    def resume_project(project_id: str) -> SuccessResponse:
        return {"ok": True, "result": service.resume(project_id)}

    @app.get("/projects/{project_id}/state", operation_id="getState", summary="Get authoritative current state", responses=ERROR_RESPONSES)
    def get_state(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_state)

    @app.get("/projects/{project_id}/unresolved", operation_id="getUnresolved", summary="Get canonical unresolved items", responses=ERROR_RESPONSES)
    def get_unresolved(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_unresolved)

    @app.get("/projects/{project_id}/rounds/{round_id}", operation_id="getRound", summary="Get one committed round", responses=ERROR_RESPONSES)
    def get_round(project_id: str, round_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_round_by_id, round_id=round_id)

    @app.post(
        "/projects/{project_id}/draft",
        operation_id="importDraft",
        summary="Import a non-authoritative structured draft",
        description="Import working draft state. This does not commit a decision or create semantic authority.",
        responses=ERROR_RESPONSES,
        openapi_extra={"x-openai-isConsequential": False},
    )
    def import_draft(project_id: str, body: DraftRequest) -> SuccessResponse:
        return _run(service, project_id, service.adapter.import_draft, draft=body.draft)

    @app.post(
        "/projects/{project_id}/preview",
        operation_id="previewDraft",
        summary="Preview the active draft without committing",
        description="Run a non-authoritative preview. This never locks or commits the draft.",
        responses=ERROR_RESPONSES,
        openapi_extra={"x-openai-isConsequential": False},
    )
    def preview_draft(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.preview_round)

    @app.post(
        "/projects/{project_id}/lock",
        operation_id="lockRound",
        summary="Commit the explicitly approved draft",
        description=(
            "Commit the currently reviewed Design Flow draft. This changes authoritative project "
            "state and should only be called after explicit owner approval."
        ),
        responses=ERROR_RESPONSES,
        openapi_extra={"x-openai-isConsequential": True},
    )
    def lock_round(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.lock_round)

    @app.get("/projects/{project_id}/context-handoff", operation_id="compileContextHandoff", summary="Compile the context handoff", responses=ERROR_RESPONSES)
    def context_handoff(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.compile_context_handoff)

    @app.get("/projects/{project_id}/living-document", operation_id="compileLivingDocument", summary="Compile the living application document", responses=ERROR_RESPONSES)
    def living_document(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.compile_living_document)

    @app.post("/projects/{project_id}/end-session", operation_id="endSession", summary="End the active session without committing a draft", responses=ERROR_RESPONSES)
    def end_session(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.end_session)

    @app.get("/projects/{project_id}/decisions", operation_id="getDecisions", summary="Get the decision ledger", responses=ERROR_RESPONSES)
    def decisions(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_decision_ledger)

    @app.get("/projects/{project_id}/concepts", operation_id="getConcepts", summary="Get Design Flow concepts", responses=ERROR_RESPONSES)
    def concepts(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_concepts)

    @app.get("/projects/{project_id}/trace", operation_id="getTrace", summary="Get immutable TRACE records", responses=ERROR_RESPONSES)
    def trace(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_trace)

    @app.get("/projects/{project_id}/session-brief", operation_id="getSessionBrief", summary="Get the engine session brief", responses=ERROR_RESPONSES)
    def session_brief(project_id: str) -> SuccessResponse:
        return _run(service, project_id, service.adapter.get_session_brief)

    return app


def _run(service: ActionService, project_id: str, operation: Any, **kwargs: Any) -> SuccessResponse:
    return {"ok": True, "result": service.on_project(project_id, operation, **kwargs)}


def _status_for(code: str) -> int:
    if code == "AUTHENTICATION_REQUIRED":
        return 401
    if code in {"PROJECT_NOT_FOUND", "ROUND_NOT_FOUND"}:
        return 404
    if code in {"NO_ACTIVE_PROJECT", "NO_ACTIVE_DRAFT", "ROUND_LOCK_FAILED"}:
        return 409
    if code in {"DRAFT_VALIDATION_FAILED", "PROJECT_VALIDATION_FAILED", "PATH_OUTSIDE_ALLOWED_ROOT"}:
        return 422
    return 500
