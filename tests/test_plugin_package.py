from __future__ import annotations

import json
import unittest
from pathlib import Path

from design_flow_mcp.tools import MUTATING_TOOLS, READ_ONLY_TOOLS


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "chatgpt" / "plugin" / "design-flow"


class PluginPackageTests(unittest.TestCase):
    def test_manifest_and_local_mcp_registration_are_complete(self) -> None:
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual("design-flow", manifest["name"])
        self.assertEqual("0.1.0", manifest["version"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertEqual("./.mcp.json", manifest["mcpServers"])
        self.assertNotIn("apps", manifest)
        self.assertLessEqual(len(manifest["interface"]["defaultPrompt"]), 3)
        for key in ("composerIcon", "logo", "logoDark"):
            self.assertTrue((PLUGIN / manifest["interface"][key]).is_file())

        config = json.loads((PLUGIN / ".mcp.json").read_text())
        server = config["mcpServers"]["design-flow"]
        self.assertEqual("design-flow-mcp", server["command"])
        self.assertNotIn("url", server)

    def test_phase_two_is_explicitly_unresolved(self) -> None:
        decisions = (ROOT / "docs" / "PHASE_2_OWNER_DECISIONS.md").read_text()
        for topic in ("Hosting", "OAuth", "Tenant", "Public submission"):
            self.assertIn(topic, decisions)
        self.assertIn("NOT READY", decisions)

    def test_plugin_does_not_add_forbidden_tool_names(self) -> None:
        exposed = READ_ONLY_TOOLS | MUTATING_TOOLS
        self.assertEqual(17, len(exposed))
        self.assertFalse(
            exposed
            & {"shell", "eval_python", "edit_decision", "rewrite_trace", "force_supersede"}
        )


if __name__ == "__main__":
    unittest.main()
