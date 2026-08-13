from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from design_flow_mcp.adapter import DesignFlowAdapter
from design_flow_mcp.config import AdapterConfig
from design_flow_mcp.tools import MUTATING_TOOLS, READ_ONLY_TOOLS, REQUIRED_TOOLS


class ToolContractTests(unittest.TestCase):
    def test_required_surface_is_present_and_raw_mutators_are_absent(self) -> None:
        exposed = READ_ONLY_TOOLS | MUTATING_TOOLS
        self.assertTrue(REQUIRED_TOOLS.issubset(exposed))
        self.assertFalse(
            exposed
            & {
                "set_state",
                "edit_decision",
                "rewrite_trace",
                "edit_project_json",
                "force_supersede",
                "mutate_concept",
                "shell",
                "eval_python",
            }
        )

    def test_getters_fail_closed_without_active_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            adapter = DesignFlowAdapter(AdapterConfig(Path(temporary).resolve()))
            response = adapter.invoke(adapter.get_state)
            self.assertFalse(response["ok"])
            self.assertEqual("NO_ACTIVE_PROJECT", response["error"]["code"])

    def test_readiness_reports_exact_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            adapter = DesignFlowAdapter(AdapterConfig(Path(temporary).resolve()))
            status = adapter.readiness()
            self.assertEqual("0.1.0", status["adapter_version"])
            self.assertEqual("0.2.0", status["engine_version"])
            self.assertTrue(status["engine_import_success"])


if __name__ == "__main__":
    unittest.main()

