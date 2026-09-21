"""The types and helpers every step builds on.

GIVEN CODE. Read it, use it, do not change it. The tests and the grader rely on it
staying exactly as it is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Chunks: the pieces of code that search returns
# ---------------------------------------------------------------------------

WHOLE_FILE = "(whole file)"
NO_CODE = "(no code was found for this question)"


@dataclass(frozen=True)
class Chunk:
    """One piece of code that search can return and the AI can be shown.

    file        path relative to corpus/requests, with forward slashes, e.g. "sessions.py"
    name        "should_strip_auth" for a function,
                "SessionRedirectMixin.should_strip_auth" for a method
    start_line  first line of the piece, counting from 1 (the first decorator line,
                if the function has decorators)
    end_line    last line of the piece, inclusive
    text        the exact source lines start_line to end_line, joined with "\\n",
                with no newline at the end
    """

    file: str
    name: str
    start_line: int
    end_line: int
    text: str

    @property
    def id(self) -> str:
        """A short unique label, e.g. "sessions.py::SessionRedirectMixin.should_strip_auth"."""
        return f"{self.file}::{self.name}"


def format_chunk(chunk: Chunk) -> str:
    """Show a chunk the way the AI sees it: a header line, then every line numbered.

    Example:
        ### sessions.py, SessionRedirectMixin.should_strip_auth, lines 127 to 157
        127:     def should_strip_auth(self, old_url, new_url):
        128:         \"\"\"Decide whether Authorization header should be removed when redirecting\"\"\"
        ...
    The line numbers are what let the AI cite a line you can check.
    """
    header = f"### {chunk.file}, {chunk.name}, lines {chunk.start_line} to {chunk.end_line}"
    numbered = [f"{chunk.start_line + i}: {line}" for i, line in enumerate(chunk.text.split("\n"))]
    return "\n".join([header, *numbered])


def whole_codebase(corpus_dir: Path) -> list[Chunk]:
    """Every .py file under corpus_dir as one chunk named "(whole file)".

    This is what the paste-everything runs send to the AI (context "whole").
    """
    chunks = []
    paths = sorted(corpus_dir.rglob("*.py"), key=lambda p: p.relative_to(corpus_dir).as_posix())
    for path in paths:
        lines = path.read_text(encoding="utf-8").split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]
        chunks.append(
            Chunk(
                file=path.relative_to(corpus_dir).as_posix(),
                name=WHOLE_FILE,
                start_line=1,
                end_line=len(lines),
                text="\n".join(lines),
            )
        )
    return chunks


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Prompt:
    """What is sent to the AI.

    system  standing instructions, the same for every question (slide 20); may be ""
    user    the part that changes with every question: the code and the question
    """

    system: str
    user: str


def build_prompt_minimal(question: str, chunks: list[Chunk]) -> Prompt:
    """The baseline prompt for Step 6: the question, the code, one line asking for JSON.

    No goal, no rules, no example. Your five-part prompt in prompt.py is compared
    against this one, so it must stay fixed for everyone.
    """
    code = "\n\n".join(format_chunk(c) for c in chunks) or NO_CODE
    user = f"{question}\n\n{code}\n\nReply in JSON with the keys answer, file and line."
    return Prompt(system="", user=user)


class BadReply(ValueError):
    """Raised by parse_reply (answer.py) when a reply is not the JSON the program asked for."""


# ---------------------------------------------------------------------------
# Words, for keyword search
# ---------------------------------------------------------------------------

# Splits identifiers the way programmers read them:
#   "should_strip_auth"    gives should, strip, auth
#   "SessionRedirectMixin" gives session, redirect, mixin
#   "HTTPAdapter"          gives http, adapter
_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")

# English words that carry no meaning for search. Code words such as "should",
# "same" or "none" are deliberately NOT in this list.
STOPWORDS = frozenset(
    """
    a an the and or but if then than so as of to in on at by for from with
    into onto about is are was were be been being am do does did doing done
    has have had having it its this that these those there here i me my we
    our you your he him his she her they them their what which who whom whose
    when where why how can could will would shall may might must not no nor
    also just very too
    """.split()
)


def words(text: str) -> list[str]:
    """Split text into lowercase words, splitting snake_case and CamelCase names.

    >>> words("Does should_strip_auth keep the HTTPAdapter header?")
    ['does', 'should', 'strip', 'auth', 'keep', 'the', 'http', 'adapter', 'header']
    """
    return [w.lower() for w in _WORD.findall(text)]
