from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from design_flow_mcp.errors import AdapterError


PROJECT_ID = re.compile(r"^prj_[0-9a-f]{32}$")


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    project_id: str
    display_name: str
    storage_key: str
    created_at: str
    updated_at: str

    def public(self) -> dict[str, str]:
        return {
            "project_id": self.project_id,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProjectRegistry:
    """Single-user routing metadata stored outside semantic project directories."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self.projects_root = self._root / "projects"
        self._state_root = self._root / ".design-flow-action-api"
        self._path = self._state_root / "registry.json"
        self._lock = RLock()
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self._state_root.mkdir(parents=True, exist_ok=True)

    def create(self, display_name: str) -> ProjectRecord:
        name = display_name.strip()
        if not name:
            raise AdapterError("PROJECT_VALIDATION_FAILED", "display_name cannot be empty")
        with self._lock:
            records = self._load()
            project_id = f"prj_{uuid4().hex}"
            now = datetime.now(UTC).isoformat()
            record = ProjectRecord(project_id, name, project_id, now, now)
            records[project_id] = record
            self._save(records)
            return record

    def remove(self, project_id: str) -> None:
        with self._lock:
            records = self._load()
            records.pop(project_id, None)
            self._save(records)

    def get(self, project_id: str) -> ProjectRecord:
        if not PROJECT_ID.fullmatch(project_id):
            raise AdapterError("PROJECT_NOT_FOUND", "Project not found")
        with self._lock:
            record = self._load().get(project_id)
        if record is None:
            raise AdapterError("PROJECT_NOT_FOUND", "Project not found")
        return record

    def list(self) -> list[ProjectRecord]:
        with self._lock:
            return sorted(self._load().values(), key=lambda item: item.created_at)

    def _load(self) -> dict[str, ProjectRecord]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: ProjectRecord(**value) for key, value in raw.get("projects", {}).items()}

    def _save(self, records: dict[str, ProjectRecord]) -> None:
        temporary = self._path.with_suffix(f".{uuid4().hex}.tmp")
        payload = {"version": 1, "projects": {key: asdict(value) for key, value in records.items()}}
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self._path)
