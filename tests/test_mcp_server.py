from __future__ import annotations

import asyncio
import os
import tempfile
import unittest

from mcp import Client


class MCPServerTests(unittest.TestCase):
    def test_protocol_discovery_and_readiness_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            os.environ["DESIGN_FLOW_PROJECT_ROOT"] = temporary
            from design_flow_mcp.server import mcp

            async def exercise() -> None:
                async with Client(mcp) as client:
                    listed = await client.list_tools()
                    names = {item.name for item in listed.tools}
                    self.assertIn("lock_round", names)
                    self.assertIn("preview_round", names)
                    self.assertNotIn("set_state", names)
                    tools = {item.name: item for item in listed.tools}
                    self.assertTrue(tools["preview_round"].annotations.read_only_hint)
                    self.assertFalse(tools["lock_round"].annotations.read_only_hint)
                    self.assertTrue(tools["lock_round"].annotations.destructive_hint)
                    self.assertEqual(
                        "authoritative-write",
                        tools["lock_round"].meta["design-flow/action"]["effect"],
                    )
                    self.assertTrue(
                        tools["lock_round"].meta["design-flow/action"]["requiresExplicitConfirmation"]
                    )
                    result = await client.call_tool("readiness", {})
                    assert result.structured_content is not None
                    self.assertTrue(result.structured_content["ok"])
                    self.assertEqual(
                        "0.2.0",
                        result.structured_content["result"]["engine_version"],
                    )

            asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
