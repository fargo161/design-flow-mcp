"""Adapter configuration and project-root confinement."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import AdapterError


@dataclass(slots=True, frozen=True)
class AdapterConfig:
    project_root: Path

    @classmethod
    def from_env(cls) -> "AdapterConfig":
        configured = os.environ.get("DESIGN_FLOW_PROJECT_ROOT")
        root = Path(configured) if configured else Path.cwd() / "DesignFlowProjects"
        root.mkdir(parents=True, exist_ok=True)
        return cls(root.resolve())

    def resolve_project_path(self, value: str, *, must_exist: bool = False) -> Path:
        if not value or not value.strip():
            raise AdapterError("PATH_OUTSIDE_ALLOWED_ROOT", "Project path cannot be empty")
        # MCP input is transport data, so reject traversal written with either
        # path separator regardless of the server host operating system.
        transport_parts = value.replace("\\", "/").split("/")
        supplied = Path(value)
        if ".." in transport_parts:
            raise AdapterError(
                "PATH_OUTSIDE_ALLOWED_ROOT",
                "Parent traversal is not allowed in project paths",
            )
        candidate = supplied if supplied.is_absolute() else self.project_root / supplied
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.project_root)
        except ValueError as error:
            raise AdapterError(
                "PATH_OUTSIDE_ALLOWED_ROOT",
                "Project path resolves outside DESIGN_FLOW_PROJECT_ROOT",
            ) from error
        if must_exist and not resolved.is_dir():
            raise AdapterError("PROJECT_NOT_FOUND", f"Project directory not found: {resolved}")
        return resolved
