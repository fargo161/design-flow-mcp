from __future__ import annotations

import json
import sys
from pathlib import Path


def normalized(value: object) -> object:
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    return value


def main() -> None:
    schema_path = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")
    schema = json.loads(schema_path.read_text())
    operations = []
    for operation_path in schema["paths"].values():
        for method in ("get", "post"):
            if method in operation_path:
                operations.append(operation_path[method]["operationId"])
    required = {
        "createProject", "listProjects", "resumeProject", "getState", "getUnresolved",
        "getRound", "importDraft", "previewDraft", "lockRound",
        "compileContextHandoff", "compileLivingDocument", "endSession",
    }
    assert required.issubset(operations)
    assert len(operations) == len(set(operations))
    assert schema["components"]["securitySchemes"]["APIKeyHeader"]["type"] == "apiKey"
    lock = schema["paths"]["/projects/{project_id}/lock"]["post"]
    preview = schema["paths"]["/projects/{project_id}/preview"]["post"]
    assert lock["x-openai-isConsequential"] is True
    assert "authoritative" in lock["description"]
    assert preview["x-openai-isConsequential"] is False
    assert "non-authoritative" in preview["description"]
    import_body = schema["paths"]["/projects/{project_id}/draft"]["post"]["requestBody"]
    request_ref = import_body["content"]["application/json"]["schema"]["$ref"]
    draft_request = schema["components"]["schemas"][request_ref.rsplit("/", 1)[-1]]
    draft_ref = draft_request["properties"]["draft"]["$ref"]
    draft_schema = schema["components"]["schemas"][draft_ref.rsplit("/", 1)[-1]]
    assert set(draft_schema["required"]) == {
        "draft_id", "round_id", "topic", "purpose", "questions", "decisions",
        "prerequisites", "answers", "created_at", "updated_at",
    }
    assert draft_schema.get("additionalProperties") is not True
    assert draft_schema["properties"]["answers"]["additionalProperties"] == {"type": "string"}
    if len(sys.argv) > 2:
        committed = json.loads(Path(sys.argv[2]).read_text())
        assert normalized(schema) == normalized(committed), (
            f"OpenAPI drift detected between {schema_path} and {sys.argv[2]}"
        )
    print("Custom GPT Action OpenAPI validation passed")


if __name__ == "__main__":
    main()
