from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from design_flow_mcp.adapter import DesignFlowAdapter
from design_flow_mcp.config import AdapterConfig

from helpers import draft


class ProjectLifecycleTests(unittest.TestCase):
    def test_full_lifecycle_through_adapter_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            adapter = DesignFlowAdapter(AdapterConfig(root))

            created = adapter.new_project(
                project_name="Lifecycle",
                project_path="lifecycle",
                project_id="lifecycle",
            )
            self.assertEqual("lifecycle", created["session_brief"]["project_id"])
            self.assertEqual(0, len(adapter.get_state()["decisions"]))
            self.assertEqual([], adapter.get_unresolved()["items"])

            adapter.import_draft(draft=draft())
            self.assertIsNotNone(adapter.get_round()["draft"])
            self.assertFalse(adapter.preview_round()["authoritative"])
            locked = adapter.lock_round()
            self.assertEqual("round-1", locked["round_id"])

            handoff = adapter.compile_context_handoff()
            living = adapter.compile_living_document()
            self.assertIn("decision-identity", handoff["content"])
            self.assertIn("Use location identity.", living["content"])
            self.assertFalse(adapter.recommend_next_round()["authoritative"])

            ended = adapter.end_session()
            self.assertIsNotNone(ended["ended_at"])
            resumed = adapter.resume_project(project_path="lifecycle")
            self.assertEqual("lifecycle", resumed["session_brief"]["project_id"])
            self.assertEqual(1, len(adapter.get_state()["decisions"]))
            self.assertEqual("decision-identity", adapter.get_decision_ledger()["decisions"][0]["decision_id"])
            self.assertGreater(len(adapter.get_trace()["records"]), 0)


if __name__ == "__main__":
    unittest.main()

