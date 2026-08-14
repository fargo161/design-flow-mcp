"""Dependency-free validation for the private Phase 1 plugin package."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "chatgpt" / "plugin" / "design-flow"


def main() -> None:
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())
    assert manifest["name"] == PLUGIN.name
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["skills"] == "./skills/"
    assert "apps" not in manifest
    prompts = manifest["interface"]["defaultPrompt"]
    assert 1 <= len(prompts) <= 3
    assert all(len(prompt) <= 128 for prompt in prompts)
    for field in ("composerIcon", "logo", "logoDark"):
        assert (PLUGIN / manifest["interface"][field]).is_file()

    mcp = json.loads((PLUGIN / ".mcp.json").read_text())
    server = mcp["mcpServers"]["design-flow"]
    assert server["command"] == "design-flow-mcp"
    assert "url" not in server

    skill = PLUGIN / "skills" / "design-flow-workflow" / "SKILL.md"
    text = skill.read_text()
    assert text.startswith("---\nname: design-flow-workflow\n")
    assert "[TODO:" not in text
    assert "lock_round" in text and "explicit owner approval" in text
    print("Phase 1 plugin package validation passed")


if __name__ == "__main__":
    main()
