from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from design_flow_action_api.app import create_app
from design_flow_action_api.config import ActionAPIConfig
from design_flow_mcp.errors import AdapterError
from helpers import draft


class ActionAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.secret = "test-secret-never-return-32-chars-minimum"
        app = create_app(ActionAPIConfig(Path(self.temporary.name), self.secret))
        self.client = TestClient(app)
        self.headers = {"X-API-Key": self.secret}

    def tearDown(self) -> None:
        self.client.close()
        self.temporary.cleanup()

    def create_project(self) -> str:
        response = self.client.post(
            "/projects",
            headers=self.headers,
            json={"display_name": "Example Project", "mode": "DISCOVERY"},
        )
        self.assertEqual(200, response.status_code, response.text)
        project_id = response.json()["result"]["project_id"]
        self.assertRegex(project_id, r"^prj_[0-9a-f]{32}$")
        self.assertNotIn(str(Path(self.temporary.name)), response.text)
        return project_id

    def test_full_custom_gpt_action_lifecycle_and_authority(self) -> None:
        project_id = self.create_project()

        listed = self.client.get("/projects", headers=self.headers)
        self.assertEqual(project_id, listed.json()["result"]["projects"][0]["project_id"])
        self.assertNotIn("storage_key", listed.text)

        resumed = self.client.post(f"/projects/{project_id}/resume", headers=self.headers)
        self.assertEqual(project_id, resumed.json()["result"]["session_brief"]["project_id"])
        state_before = self.client.get(f"/projects/{project_id}/state", headers=self.headers).json()
        self.assertEqual([], state_before["result"]["decisions"])
        unresolved = self.client.get(f"/projects/{project_id}/unresolved", headers=self.headers)
        self.assertEqual(0, unresolved.json()["result"]["count"])

        imported = self.client.post(
            f"/projects/{project_id}/draft", headers=self.headers, json={"draft": draft()}
        )
        self.assertFalse(imported.json()["result"]["authoritative"])
        after_import = self.client.get(f"/projects/{project_id}/state", headers=self.headers).json()
        self.assertEqual([], after_import["result"]["decisions"])

        preview = self.client.post(f"/projects/{project_id}/preview", headers=self.headers)
        self.assertFalse(preview.json()["result"]["authoritative"])
        after_preview = self.client.get(f"/projects/{project_id}/state", headers=self.headers).json()
        self.assertEqual([], after_preview["result"]["decisions"])

        locked = self.client.post(f"/projects/{project_id}/lock", headers=self.headers)
        self.assertEqual(200, locked.status_code, locked.text)
        self.assertTrue(locked.json()["result"]["committed"])
        self.assertEqual(1, len(locked.json()["result"]["current_state"]["decisions"]))

        committed_round = self.client.get(
            f"/projects/{project_id}/rounds/round-1", headers=self.headers
        )
        self.assertEqual("round-1", committed_round.json()["result"]["round_id"])
        handoff = self.client.get(f"/projects/{project_id}/context-handoff", headers=self.headers)
        living = self.client.get(f"/projects/{project_id}/living-document", headers=self.headers)
        self.assertIn("decision-identity", handoff.json()["result"]["content"])
        self.assertIn("Use location identity.", living.json()["result"]["content"])
        ended = self.client.post(f"/projects/{project_id}/end-session", headers=self.headers)
        self.assertFalse(ended.json()["result"]["project_complete"])

    def test_lock_failures_preserve_authority_and_draft(self) -> None:
        project_id = self.create_project()
        no_draft = self.client.post(f"/projects/{project_id}/lock", headers=self.headers)
        self.assertEqual(409, no_draft.status_code)

        self.client.post(
            f"/projects/{project_id}/draft",
            headers=self.headers,
            json={"draft": draft(complete=False)},
        )
        failed = self.client.post(f"/projects/{project_id}/lock", headers=self.headers)
        self.assertEqual(409, failed.status_code)
        self.assertEqual("ROUND_LOCK_FAILED", failed.json()["error"]["code"])
        self.assertEqual(
            "The draft could not be committed; it remains available for review.",
            failed.json()["error"]["message"],
        )
        self.assertNotIn("details", failed.json()["error"])
        state = self.client.get(f"/projects/{project_id}/state", headers=self.headers).json()
        self.assertEqual([], state["result"]["decisions"])

    def test_authentication_fails_before_lookup_and_secret_is_not_logged(self) -> None:
        with self.assertLogs("design_flow_action_api", level=logging.WARNING) as captured:
            missing = self.client.get("/projects/not-a-project/state")
            wrong = self.client.get(
                "/projects/not-a-project/state", headers={"X-API-Key": "wrong-secret"}
            )
        self.assertEqual(401, missing.status_code)
        self.assertEqual(401, wrong.status_code)
        log_text = "\n".join(captured.output)
        self.assertNotIn(self.secret, log_text)
        self.assertNotIn("wrong-secret", log_text)
        self.assertNotIn(self.secret, missing.text + wrong.text)

    def test_project_identifier_rejects_path_injection_and_hides_paths(self) -> None:
        self.create_project()
        for injected in ("../escape", "%2e%2e%2fescape", "C:%5CWindows"):
            response = self.client.get(f"/projects/{injected}/state", headers=self.headers)
            self.assertIn(response.status_code, {404, 405})
            self.assertNotIn(str(Path(self.temporary.name)), response.text)

    def test_openapi_contract_is_action_ready(self) -> None:
        schema = self.client.app.openapi()
        operations = {
            value[method]["operationId"]
            for value in schema["paths"].values()
            for method in value
            if method in {"get", "post"}
        }
        required = {
            "createProject", "listProjects", "resumeProject", "getState", "getUnresolved",
            "getRound", "importDraft", "previewDraft", "lockRound",
            "compileContextHandoff", "compileLivingDocument", "endSession",
        }
        self.assertTrue(required.issubset(operations))
        self.assertEqual(len(operations), len(set(operations)))
        schemes = schema["components"]["securitySchemes"]
        self.assertEqual("apiKey", schemes["APIKeyHeader"]["type"])
        lock = schema["paths"]["/projects/{project_id}/lock"]["post"]
        preview = schema["paths"]["/projects/{project_id}/preview"]["post"]
        self.assertTrue(lock["x-openai-isConsequential"])
        self.assertIn("authoritative", lock["description"])
        self.assertFalse(preview["x-openai-isConsequential"])
        self.assertIn("non-authoritative", preview["description"])

    def test_registry_is_outside_native_project_and_contains_no_secret(self) -> None:
        project_id = self.create_project()
        root = Path(self.temporary.name)
        registry = root / ".design-flow-action-api" / "registry.json"
        project = root / "projects" / project_id
        self.assertTrue(registry.is_file())
        self.assertTrue(project.is_dir())
        self.assertNotIn(self.secret, registry.read_text())
        semantic_text = "".join(
            path.read_text(errors="ignore") for path in project.rglob("*") if path.is_file()
        )
        self.assertNotIn(self.secret, semantic_text)
        self.assertNotIn(".design-flow-action-api", semantic_text)

    def test_error_response_sanitizes_physical_project_paths(self) -> None:
        project_id = self.create_project()
        root = str(Path(self.temporary.name).resolve())
        physical = str(Path(root) / "projects" / project_id / "manifest.json")
        service = self.client.app.state.service

        def leaking_operation() -> dict[str, object]:
            raise AdapterError(
                "PROJECT_VALIDATION_FAILED",
                f"Validation failed while reading {physical} below {root}",
                {"physical_path": physical},
            )

        original = service.adapter.get_state
        service.adapter.get_state = leaking_operation
        try:
            response = self.client.get(f"/projects/{project_id}/state", headers=self.headers)
        finally:
            service.adapter.get_state = original

        self.assertEqual(422, response.status_code)
        self.assertEqual("PROJECT_VALIDATION_FAILED", response.json()["error"]["code"])
        self.assertEqual(
            "The project failed integrity validation.", response.json()["error"]["message"]
        )
        self.assertNotIn(root, response.text)
        self.assertNotIn(physical, response.text)
        self.assertNotIn("Traceback", response.text)

    def test_api_key_must_be_at_least_32_characters(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 32 characters"):
            ActionAPIConfig(Path(self.temporary.name), "too-short")

    def test_openapi_drift_validator_rejects_an_intentional_mismatch(self) -> None:
        generated = Path(self.temporary.name) / "generated.json"
        committed = Path(self.temporary.name) / "committed.json"
        schema = self.client.app.openapi()
        generated.write_text(json.dumps(schema), encoding="utf-8")
        schema["info"]["title"] = "Intentional drift"
        committed.write_text(json.dumps(schema), encoding="utf-8")
        validator = Path(__file__).parents[1] / "scripts" / "validate_action_openapi.py"

        result = subprocess.run(
            [sys.executable, str(validator), str(generated), str(committed)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("OpenAPI drift detected", result.stderr)


if __name__ == "__main__":
    unittest.main()
