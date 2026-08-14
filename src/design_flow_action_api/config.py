from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ActionAPIConfig:
    project_root: Path
    api_key: str
    host: str = "127.0.0.1"
    port: int = 8080
    public_base_url: str = "http://127.0.0.1:8080"

    @classmethod
    def from_env(cls) -> "ActionAPIConfig":
        root = Path(os.environ.get("DESIGN_FLOW_PROJECT_ROOT", Path.cwd() / "DesignFlowProjects"))
        key = os.environ.get("DESIGN_FLOW_API_KEY", "")
        if len(key) < 32:
            raise RuntimeError("DESIGN_FLOW_API_KEY must contain at least 32 characters")
        root.mkdir(parents=True, exist_ok=True)
        return cls(
            project_root=root.resolve(),
            api_key=key,
            host=os.environ.get("DESIGN_FLOW_API_HOST", "127.0.0.1"),
            port=int(os.environ.get("DESIGN_FLOW_API_PORT", "8080")),
            public_base_url=os.environ.get(
                "DESIGN_FLOW_PUBLIC_BASE_URL", "http://127.0.0.1:8080"
            ).rstrip("/"),
        )

    def __post_init__(self) -> None:
        if len(self.api_key) < 32:
            raise ValueError("DESIGN_FLOW_API_KEY must contain at least 32 characters")
