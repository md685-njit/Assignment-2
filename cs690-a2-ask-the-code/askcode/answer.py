"""Step 4, part B: check the AI's reply before your program trusts it.

YOUR CODE. Read HANDOUT.md, Step 4, first.
Check your work with:  pytest tests/test_answer.py
"""

from __future__ import annotations

import json  # noqa: F401  (you will need it)

from askcode.core import BadReply  # noqa: F401  (raise this for every bad reply)


def parse_reply(text: str) -> dict:
    """Check the model's reply and return {"answer": ..., "file": ..., "line": ...}.

    Accept the reply only if every rule holds. Otherwise raise BadReply with a short
    message that says which rule failed. Never let a different exception escape.

    1. After stripping whitespace, the reply is one JSON object. The only thing
       allowed around it is a single Markdown code fence: a first line of ``` or
       ```json, and a last line of ```. Any other text before or after the object
       makes the reply bad.
    2. The object has exactly the keys "answer", "file" and "line": none missing,
       none extra.
    3. "answer" is a string that is not empty or only whitespace.
    4. "file" is a non-empty string or null. "line" is an integer or null; true and
       false do not count as integers, and an integer line must be at least 1.
    5. "file" and "line" are both null, or both set.

    Return a new dict with exactly the three keys and the values from the reply.
    """
    raise NotImplementedError("Step 4: write parse_reply in askcode/answer.py")
