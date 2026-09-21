"""Public tests for Step 4, part A (askcode/prompt.py). Run: pytest tests/test_prompt.py"""

import json
import re

from askcode.core import NO_CODE, Chunk, format_chunk
from askcode.prompt import build_prompt_five_part

LABELS = ["Goal:", "Inputs and outputs:", "Rules:", "Example:", "Reply format:"]

A = Chunk(file="sessions.py", name="Session.close", start_line=10, end_line=11, text="def close(self):\n    pass")
B = Chunk(file="api.py", name="get", start_line=60, end_line=61, text="def get(url):\n    return url")


def label_positions(system: str) -> list[int]:
    positions = []
    for label in LABELS:
        match = re.search(r"(?m)^" + re.escape(label), system)
        assert match, f"prompt.system has no line starting with {label!r}"
        positions.append(match.start())
    return positions


def test_five_labels_in_order():
    positions = label_positions(build_prompt_five_part("Where is close?", [A]).system)
    assert positions == sorted(positions)


def test_system_is_the_same_for_every_question_and_every_context():
    first = build_prompt_five_part("Where is close?", [A]).system
    assert build_prompt_five_part("How does get work?", [B, A]).system == first
    assert build_prompt_five_part("Anything?", []).system == first


def test_rules_cover_the_not_found_case():
    system = build_prompt_five_part("q", [A]).system
    assert "not found in the code shown" in system
    assert "null" in system


def test_reply_format_names_the_three_keys():
    system = build_prompt_five_part("q", [A]).system
    reply_format = system[label_positions(system)[4]:]
    for key in ('"answer"', '"file"', '"line"'):
        assert key in reply_format


def test_example_contains_a_valid_json_reply():
    system = build_prompt_five_part("q", [A]).system
    starts = label_positions(system)
    example = system[starts[3]:starts[4]]
    replies = []
    for candidate in re.findall(r"\{[^{}]*\}", example):
        try:
            replies.append(json.loads(candidate))
        except json.JSONDecodeError:
            pass
    assert any(isinstance(r, dict) and set(r) == {"answer", "file", "line"} for r in replies)


def test_user_has_code_then_question_last():
    question = "How does get work?"
    user = build_prompt_five_part(question, [A, B]).user
    code_at = user.index("Code:")
    a_at, b_at = user.index(format_chunk(A)), user.index(format_chunk(B))
    question_label_at = user.index("Question:")
    assert code_at < a_at < b_at < question_label_at
    assert user.rstrip().endswith(question)


def test_empty_context_says_no_code():
    user = build_prompt_five_part("Anything?", []).user
    assert NO_CODE in user
    assert user.index("Code:") < user.index(NO_CODE) < user.index("Question:")
