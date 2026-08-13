from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from design_flow_mcp.adapter import DesignFlowAdapter
from design_flow_mcp.config import AdapterConfig
from design_flow_mcp.errors import AdapterError


class ErrorAndPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.config = AdapterConfig(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_allowed_relative_project_path_is_accepted(self) -> None:
        self.assertEqual(self.root / "safe", self.config.resolve_project_path("safe"))

    def test_parent_traversal_is_rejected_for_both_transport_separators(self) -> None:
        for value in ("../escape", "..\\escape"):
            with self.subTest(value=value):
                with self.assertRaises(AdapterError) as raised:
                    self.config.resolve_project_path(value)
                self.assertEqual("PATH_OUTSIDE_ALLOWED_ROOT", raised.exception.code)

    def test_absolute_escape_is_rejected(self) -> None:
        with self.assertRaises(AdapterError) as raised:
            self.config.resolve_project_path(str(self.root.parent / "escape"))
        self.assertEqual("PATH_OUTSIDE_ALLOWED_ROOT", raised.exception.code)

    def test_invalid_project_load_returns_structured_category(self) -> None:
        broken = self.root / "broken"
        broken.mkdir()
        adapter = DesignFlowAdapter(self.config)
        response = adapter.invoke(adapter.resume_project, project_path="broken")
        self.assertFalse(response["ok"])
        self.assertIn(
            response["error"]["code"],
            {"PROJECT_VALIDATION_FAILED", "ENGINE_INTEGRITY_ERROR"},
        )

    def test_draft_file_cannot_escape_root(self) -> None:
        adapter = DesignFlowAdapter(self.config)
        adapter.new_project(project_name="Safe", project_path="safe")
        response = adapter.invoke(
            adapter.import_draft, draft_file_path=str(self.root.parent / "outside.json")
        )
        self.assertFalse(response["ok"])
        self.assertEqual("PATH_OUTSIDE_ALLOWED_ROOT", response["error"]["code"])


if __name__ == "__main__":
    unittest.main()
