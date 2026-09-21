"""Public tests for Step 4, part B (askcode/answer.py). Run: pytest tests/test_answer.py"""

import pytest

from askcode.answer import parse_reply
from askcode.core import BadReply

GOOD = '{"answer": "It keeps the header.", "file": "sessions.py", "line": 137}'


def test_plain_json_object():
    assert parse_reply(GOOD) == {"answer": "It keeps the header.", "file": "sessions.py", "line": 137}


def test_whitespace_around_is_fine():
    assert parse_reply("\n  " + GOOD + "  \n")["line"] == 137


def test_json_code_fence_is_fine():
    assert parse_reply("```json\n" + GOOD + "\n```")["file"] == "sessions.py"


def test_not_found_reply_with_nulls():
    reply = '{"answer": "not found in the code shown", "file": null, "line": null}'
    assert parse_reply(reply) == {"answer": "not found in the code shown", "file": None, "line": None}


@pytest.mark.parametrize(
    "reply",
    [
        "Here is the answer: " + GOOD,
        GOOD + " Hope this helps!",
        '{"answer": "x", "file": "a.py"}',
        '{"answer": "x", "file": "a.py", "line": 3, "confidence": 0.9}',
        '{"answer": "x", "file": "a.py", "line": "3"}',
        '{"answer": "x", "file": "a.py", "line": true}',
        '{"answer": "x", "file": "a.py", "line": 0}',
        '{"answer": "", "file": "a.py", "line": 3}',
        '{"answer": "x", "file": "a.py", "line": null}',
        '["answer", "file", "line"]',
        "not json at all",
    ],
)
def test_bad_replies_raise_badreply(reply):
    with pytest.raises(BadReply):
        parse_reply(reply)
