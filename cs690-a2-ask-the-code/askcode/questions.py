"""Load and check questions/questions.json.

GIVEN CODE. Do not change it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from askcode import QUESTIONS_FILE

FIELDS = ("id", "question", "expected_file", "expected_function", "expected_answer")


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    expected_file: str | None
    expected_function: str | None
    expected_answer: str

    @property
    def answerable(self) -> bool:
        """False for a question the code cannot answer (expected_file is null)."""
        return self.expected_file is not None


def load_questions(path: Path | str = QUESTIONS_FILE) -> list[Question]:
    """Read the questions file and check its shape. Raises ValueError on any problem."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError(f"{path} must hold a non-empty JSON list of question objects.")

    questions: list[Question] = []
    seen: set[str] = set()
    for number, item in enumerate(data, start=1):
        where = f"question {number} in {path.name}"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be a JSON object.")
        if set(item) != set(FIELDS):
            raise ValueError(f"{where} must have exactly these keys: {', '.join(FIELDS)}.")
        for key in ("id", "question", "expected_answer"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{where}: {key} must be a non-empty string.")
        exp_file, exp_func = item["expected_file"], item["expected_function"]
        both_null = exp_file is None and exp_func is None
        both_set = (
            isinstance(exp_file, str) and exp_file.strip() != ""
            and isinstance(exp_func, str) and exp_func.strip() != ""
        )
        if not (both_null or both_set):
            raise ValueError(
                f"{where}: expected_file and expected_function must both be strings, "
                "or both be null for a question the code cannot answer."
            )
        if item["id"] in seen:
            raise ValueError(f"{where}: the id {item['id']!r} is used twice.")
        seen.add(item["id"])
        questions.append(Question(**{key: item[key] for key in FIELDS}))
    return questions
