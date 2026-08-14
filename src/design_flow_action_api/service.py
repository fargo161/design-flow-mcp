from __future__ import annotations

from threading import RLock
from typing import Any, Callable

from design_flow_mcp.adapter import DesignFlowAdapter
from design_flow_mcp.config import AdapterConfig
from design_flow_mcp.errors import AdapterError

from .registry import ProjectRecord, ProjectRegistry


class ActionService:
    """Serialized single-user orchestration over the existing safe adapter."""

    def __init__(self, root: Any) -> None:
        self.registry = ProjectRegistry(root)
        self.adapter = DesignFlowAdapter(AdapterConfig(self.registry.projects_root.resolve()))
        self._lock = RLock()

    def create_project(self, *, display_name: str, mode: str, description: str) -> dict[str, Any]:
        with self._lock:
            record = self.registry.create(display_name)
            try:
                created = self.adapter.new_project(
                    project_name=display_name,
                    project_path=record.storage_key,
                    project_id=record.project_id,
                    mode=mode,
                    description=description,
                )
            except Exception:
                self.registry.remove(record.project_id)
                raise
            return {**record.public(), "session_brief": created["session_brief"]}

    def list_projects(self) -> dict[str, Any]:
        projects = [record.public() for record in self.registry.list()]
        return {"projects": projects, "count": len(projects)}

    def on_project(self, project_id: str, operation: Callable[..., dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            record = self._activate(project_id)
            result = operation(**kwargs)
            return self._scrub(result, record)

    def resume(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            record = self.registry.get(project_id)
            result = self.adapter.resume_project(project_path=record.storage_key)
            return {**record.public(), "session_brief": result["session_brief"]}

    def _activate(self, project_id: str) -> ProjectRecord:
        record = self.registry.get(project_id)
        active = self.adapter.project
        if active is None or active.workspace.project.project_id != record.project_id:
            self.adapter.resume_project(project_path=record.storage_key)
        return record

    @staticmethod
    def _scrub(value: Any, record: ProjectRecord) -> Any:
        if isinstance(value, dict):
            return {
                key: ActionService._scrub(item, record)
                for key, item in value.items()
                if key not in {"project_path", "allowed_project_root", "storage_key"}
            }
        if isinstance(value, list):
            return [ActionService._scrub(item, record) for item in value]
        return value
