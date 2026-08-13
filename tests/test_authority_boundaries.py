from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from design_flow_mcp.adapter import DesignFlowAdapter
from design_flow_mcp.config import AdapterConfig

from helpers import draft


class AuthorityBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name).resolve()
        self.adapter = DesignFlowAdapter(AdapterConfig(root))
        self.adapter.new_project(project_name="Authority", project_path="authority")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_import_and_preview_do_not_change_authority(self) -> None:
        project = self.adapter.project
        assert project is not None
        decisions_before = tuple(project.workspace.ledger.decisions)
        trace_before = tuple(project.workspace.trace.records)

        result = self.adapter.import_draft(draft=draft())
        self.assertFalse(result["authoritative"])
        self.assertEqual(decisions_before, project.workspace.ledger.decisions)
        self.assertEqual(trace_before, project.workspace.trace.records)

        preview = self.adapter.preview_round()
        self.assertFalse(preview["authoritative"])
        self.assertEqual("DRAFT_PREVIEW", preview["status"])
        self.assertEqual(decisions_before, project.workspace.ledger.decisions)
        self.assertEqual(trace_before, project.workspace.trace.records)

    def test_failed_lock_preserves_draft_and_authority(self) -> None:
        project = self.adapter.project
        assert project is not None
        self.adapter.import_draft(draft=draft(complete=False))
        response = self.adapter.invoke(self.adapter.lock_round)
        self.assertFalse(response["ok"])
        self.assertEqual("ROUND_LOCK_FAILED", response["error"]["code"])
        self.assertTrue(response["error"]["details"]["draft_preserved"])
        self.assertIsNotNone(project.draft)
        self.assertEqual(0, len(project.workspace.ledger.decisions))

    def test_successful_lock_uses_engine_authority_path(self) -> None:
        project = self.adapter.project
        assert project is not None
        self.adapter.import_draft(draft=draft())
        result = self.adapter.lock_round()
        self.assertTrue(result["committed"])
        self.assertIsNone(project.draft)
        self.assertEqual(1, len(project.workspace.ledger.decisions))
        actions = [item.action.value for item in project.workspace.trace.records]
        self.assertIn("SYNTHESIZE", actions)
        self.assertIn("REGISTER_DECISION", actions)


if __name__ == "__main__":
    unittest.main()

