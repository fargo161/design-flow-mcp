from __future__ import annotations

from typing import Any


def draft(*, complete: bool = True, round_id: str = "round-1") -> dict[str, Any]:
    return {
        "draft_id": f"draft-{round_id}",
        "round_id": round_id,
        "topic": "Identity",
        "purpose": "Choose the operative identity.",
        "questions": [
            {
                "question_id": "question-identity",
                "text": "Which identity?",
                "question_type": "MULTIPLE_CHOICE",
                "options": [
                    {"key": "A", "label": "Actor"},
                    {"key": "B", "label": "Location"},
                ],
                "recommendation": {
                    "proposed_answer": ["A"],
                    "reason": "Actor identity is the smallest first step.",
                    "status": "PROPOSED",
                },
            }
        ],
        "decisions": [
            {
                "question_id": "question-identity",
                "decision_id": "decision-identity",
                "scope": "identity",
                "rule_mapping": [
                    {"key": ["A"], "rule": "Use actor identity."},
                    {"key": ["B"], "rule": "Use location identity."},
                ],
                "dependencies": [],
                "unresolved_consequences": [],
                "supersedes_decision": None,
                "supersession_notes": "",
                "concept": None,
            }
        ],
        "prerequisites": [],
        "answers": {"question-identity": "B"} if complete else {},
        "created_at": "2026-08-13T12:00:00Z",
        "updated_at": "2026-08-13T12:00:00Z",
    }

