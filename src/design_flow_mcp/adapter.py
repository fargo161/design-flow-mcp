"""Narrow orchestration facade over public Design Flow engine APIs."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import design_flow
from design_flow import (
    DesignFlowMode,
    PersistentProject,
    ProjectValidationError,
    compile_context_handoff,
    compile_unresolved_register,
    recommend_next_round,
)

from . import ENGINE_BASELINE, ENGINE_VERSION, __version__
from .config import AdapterConfig
from .errors import AdapterError


def _value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_value(item) for item in value]
    return value


class DesignFlowAdapter:
    """One active Design Flow project/session per server process."""

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config
        self.project: PersistentProject | None = None

    def readiness(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "adapter_version": __version__,
            "engine_version": getattr(design_flow, "__version__", "unknown"),
            "expected_engine_version": ENGINE_VERSION,
            "engine_baseline": ENGINE_BASELINE,
            "engine_import_success": True,
            "allowed_project_root": str(self.config.project_root),
            "active_project": self.project is not None,
        }

    def new_project(
        self,
        *,
        project_name: str,
        project_path: str,
        project_id: str | None = None,
        mode: str = "DISCOVERY",
        description: str = "",
    ) -> dict[str, Any]:
        path = self.config.resolve_project_path(project_path)
        try:
            parsed_mode = DesignFlowMode(mode.upper())
            identifier = project_id or self._slug(project_name)
            project = PersistentProject.create(
                path,
                project_id=identifier,
                name=project_name,
                description=description or f"Design Flow project: {project_name}",
                mode=parsed_mode,
                authority="Only an explicit owner-approved lock creates authority.",
            )
            project.start_session()
        except (OSError, TypeError, ValueError, ProjectValidationError) as error:
            raise AdapterError("ENGINE_INTEGRITY_ERROR", str(error)) from error
        self.project = project
        return {"project_path": str(path), "session_brief": self.get_session_brief()}

    def resume_project(self, *, project_path: str) -> dict[str, Any]:
        path = self.config.resolve_project_path(project_path, must_exist=True)
        try:
            project = PersistentProject.resume(path)
            if project.active_session is None:
                project.start_session()
        except ProjectValidationError as error:
            raise AdapterError("PROJECT_VALIDATION_FAILED", str(error)) from error
        except (OSError, TypeError, ValueError) as error:
            raise AdapterError("ENGINE_INTEGRITY_ERROR", str(error)) from error
        self.project = project
        return {"project_path": str(path), "session_brief": self.get_session_brief()}

    def get_state(self) -> dict[str, Any]:
        project = self._active()
        state = project.workspace.state_compiler.compile(
            project.workspace.project, project.workspace.ledger
        )
        return {
            "project_id": state.project_id,
            "version": state.version,
            "decisions": [self._decision(item) for item in state.decisions],
            "unresolved": list(state.unresolved),
            "summary": f"{len(state.decisions)} current decisions; {len(state.unresolved)} unresolved items",
        }

    def get_unresolved(self) -> dict[str, Any]:
        items = compile_unresolved_register(self._active().workspace)
        return {"items": list(items), "count": len(items), "compiler": "design_flow.compile_unresolved_register"}

    def get_round(self) -> dict[str, Any]:
        project = self._active()
        committed = project.workspace.rounds.rounds
        draft = project.draft
        return {
            "draft": None if draft is None else self._draft(draft),
            "last_committed": None if not committed else self._round(committed[-1]),
            "committed_round_count": len(committed),
        }

    def get_round_by_id(self, *, round_id: str) -> dict[str, Any]:
        """Return one immutable committed round without exposing registry internals."""
        for item in self._active().workspace.rounds.rounds:
            if item.round_id == round_id:
                return self._round(item)
        raise AdapterError("ROUND_NOT_FOUND", f"Committed round not found: {round_id}")

    def import_draft(
        self,
        *,
        draft: dict[str, Any] | None = None,
        draft_file_path: str | None = None,
    ) -> dict[str, Any]:
        project = self._active()
        if (draft is None) == (draft_file_path is None):
            raise AdapterError(
                "DRAFT_VALIDATION_FAILED",
                "Provide exactly one of draft or draft_file_path",
            )
        temporary: Path | None = None
        try:
            if draft is not None:
                temporary = project.path / f".design-flow-mcp-intake-{uuid4().hex}.json"
                temporary.write_text(json.dumps(draft), encoding="utf-8")
                imported = project.import_draft(temporary)
            else:
                source = self.config.resolve_project_path(str(draft_file_path), must_exist=False)
                if not source.is_file():
                    raise AdapterError("PROJECT_NOT_FOUND", f"Draft file not found: {source}")
                imported = project.import_draft(source)
        except AdapterError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise AdapterError("DRAFT_VALIDATION_FAILED", str(error)) from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"authoritative": False, "committed": False, "draft": self._draft(imported)}

    def preview_round(self) -> dict[str, Any]:
        project = self._active()
        self._require_draft(project)
        preview = project.preview_draft()
        return {
            "authoritative": False,
            "status": "DRAFT_PREVIEW",
            "derived_rules": list(preview.derived_rules),
            "potential_conflicts": list(preview.errors),
            "potential_supersession": list(preview.potential_supersessions),
            "affected_concepts": list(preview.affected_concepts),
            "unresolved_implications": list(preview.unresolved),
        }

    def lock_round(self) -> dict[str, Any]:
        project = self._active()
        self._require_draft(project)
        try:
            committed = project.lock_draft()
        except ProjectValidationError as error:
            raise AdapterError(
                "ROUND_LOCK_FAILED",
                str(error),
                {"draft_preserved": project.draft is not None},
            ) from error
        recommendation = recommend_next_round(project.workspace)
        return {
            "committed": True,
            "round_id": committed.round_id,
            "save_generation": project.manifest.save_generation,
            "current_state": self.get_state(),
            "unresolved": self.get_unresolved(),
            "next_round_recommendation": {
                "authoritative": False,
                "recommendation": recommendation.topic,
                "reason": recommendation.reason,
            },
        }

    def compile_context_handoff(self) -> dict[str, Any]:
        project = self._active()
        return {
            "artifact": "context_handoff",
            "content": compile_context_handoff(project.workspace, project.sessions),
            "authoritative_source": "design_flow.compile_context_handoff",
        }

    def compile_living_document(self) -> dict[str, Any]:
        project = self._active()
        return {
            "artifact": "living_application",
            "content": project.workspace.render_application_document(),
            "authoritative_source": "DesignFlowWorkspace.render_application_document",
        }

    def recommend_next_round(self) -> dict[str, Any]:
        recommendation = recommend_next_round(self._active().workspace)
        return {
            "authoritative": False,
            "recommendation": recommendation.topic,
            "reason": recommendation.reason,
            "round_started": False,
        }

    def end_session(self) -> dict[str, Any]:
        project = self._active()
        try:
            session = project.end_session()
        except (OSError, TypeError, ValueError, ProjectValidationError) as error:
            raise AdapterError("ENGINE_INTEGRITY_ERROR", str(error)) from error
        return {
            "session_id": session.session_id,
            "ended_at": session.ended_at,
            "rounds_committed": list(session.rounds_committed),
            "draft_retained": project.draft is not None,
            "project_complete": False,
        }

    def get_decision_ledger(self) -> dict[str, Any]:
        decisions = self._active().workspace.ledger.decisions
        return {"decisions": [self._decision(item) for item in decisions], "count": len(decisions)}

    def get_concepts(self) -> dict[str, Any]:
        registry = self._active().workspace.concepts
        items = (*registry.concepts, *registry.affected, *registry.history)
        return {
            "concepts": [
                {
                    "concept_id": item.concept_id,
                    "name": item.canonical_name,
                    "version": item.version,
                    "status": item.status.value,
                    "maturity": item.maturity.value,
                    "definition": item.definition,
                    "source_decisions": list(item.source_decisions),
                    "unresolved": list(item.unresolved),
                }
                for item in items
            ]
        }

    def get_trace(self) -> dict[str, Any]:
        records = self._active().workspace.trace.records
        return {
            "records": [
                {
                    "trace_id": item.trace_id,
                    "action": item.action.value,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "details": _value(item.details),
                }
                for item in records
            ]
        }

    def get_session_brief(self) -> dict[str, Any]:
        brief = self._active().session_brief()
        return {
            "project_id": brief.project_id,
            "name": brief.name,
            "mode": brief.mode,
            "current_rules": list(brief.current_rules),
            "unresolved": list(brief.unresolved),
            "last_completed_round": brief.last_completed_round,
            "recommended_next_round": brief.recommended_next_round,
            "recommendation_reason": brief.recommendation_reason,
            "design_flow_session_id": self._active().active_session_id,
        }

    def invoke(self, operation: Callable[..., dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        try:
            return {"ok": True, "result": operation(**kwargs)}
        except AdapterError as error:
            return {"ok": False, "error": error.as_dict()}
        except Exception as error:  # Fail closed at the transport boundary.
            return {
                "ok": False,
                "error": {"code": "ENGINE_INTEGRITY_ERROR", "message": str(error)},
            }

    def _active(self) -> PersistentProject:
        if self.project is None:
            raise AdapterError("NO_ACTIVE_PROJECT", "Open or create a project first")
        return self.project

    @staticmethod
    def _require_draft(project: PersistentProject) -> None:
        if project.draft is None:
            raise AdapterError("NO_ACTIVE_DRAFT", "Import a draft first")

    @staticmethod
    def _slug(value: str) -> str:
        slug = "-".join(value.lower().split())
        return "".join(char for char in slug if char.isalnum() or char in "-_") or f"project-{uuid4().hex[:8]}"

    @staticmethod
    def _decision(item: Any) -> dict[str, Any]:
        return {
            "decision_id": item.decision_id,
            "canonical_rule": item.canonical_rule,
            "authoritative_value": list(item.authoritative_value),
            "status": item.status.value,
            "scope": item.scope,
            "source_round": item.source_round,
            "source_question": item.source_question,
            "supersedes": list(item.supersedes),
            "unresolved_consequences": list(item.unresolved_consequences),
        }

    @staticmethod
    def _draft(item: Any) -> dict[str, Any]:
        return {
            "draft_id": item.draft_id,
            "round_id": item.round_id,
            "topic": item.topic,
            "purpose": item.purpose,
            "complete": item.complete,
            "question_ids": [question.question_id for question in item.questions],
            "answered_question_ids": list(item.answers),
        }

    @staticmethod
    def _round(item: Any) -> dict[str, Any]:
        return {
            "round_id": item.round_id,
            "topic": item.topic,
            "purpose": item.purpose,
            "status": item.status.value,
            "derived_rules": list(item.derived_rules),
            "unresolved": list(item.unresolved),
        }
