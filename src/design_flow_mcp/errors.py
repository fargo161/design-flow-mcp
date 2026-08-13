"""Stable adapter error categories suitable for MCP clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AdapterError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


def failure(error: AdapterError) -> dict[str, Any]:
    return {"ok": False, "error": error.as_dict()}


def success(result: Any) -> dict[str, Any]:
    return {"ok": True, "result": result}

