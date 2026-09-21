"""Public tests for Step 2 (askcode/split.py). Run: pytest tests/test_split.py"""

from pathlib import Path

from askcode import CORPUS_DIR
from askcode.split import split_corpus, split_file


def write(tmp_path: Path, relative: str, source: str) -> Path:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


SAMPLE = (
    "import os\n"                     # 1
    "\n"                              # 2
    "LIMIT = 3\n"                     # 3
    "\n"                              # 4
    "def top(x):\n"                   # 5
    "    return x + 1\n"              # 6
    "\n"                              # 7
    "class Box:\n"                    # 8
    "    size = 2\n"                  # 9
    "\n"                              # 10
    "    def open(self):\n"           # 11
    "        return 'open'\n"         # 12
    "\n"                              # 13
    "    @property\n"                 # 14
    "    def label(self):\n"          # 15
    "        return 'box'\n"          # 16
)


def test_names_for_functions_and_methods(tmp_path):
    path = write(tmp_path, "sample.py", SAMPLE)
    assert [c.name for c in split_file(path, tmp_path)] == ["top", "Box.open", "Box.label"]


def test_line_numbers_and_exact_text(tmp_path):
    path = write(tmp_path, "sample.py", SAMPLE)
    top, box_open, _ = split_file(path, tmp_path)
    assert (top.start_line, top.end_line) == (5, 6)
    assert top.text == "def top(x):\n    return x + 1"
    assert (box_open.start_line, box_open.end_line) == (11, 12)
    assert box_open.text == "    def open(self):\n        return 'open'"


def test_decorator_line_starts_the_chunk(tmp_path):
    path = write(tmp_path, "sample.py", SAMPLE)
    label = split_file(path, tmp_path)[2]
    assert (label.start_line, label.end_line) == (14, 16)
    assert label.text.split("\n")[0] == "    @property"


def test_file_is_relative_with_forward_slashes(tmp_path):
    path = write(tmp_path, "pkg/inner/mod.py", "def f():\n    pass\n")
    assert split_file(path, tmp_path)[0].file == "pkg/inner/mod.py"


def test_code_outside_functions_is_not_a_chunk(tmp_path):
    path = write(tmp_path, "consts.py", "A = 1\nB = 2\n\nclass Empty:\n    pass\n")
    assert split_file(path, tmp_path) == []


def test_corpus_has_230_chunks():
    assert len(split_corpus(CORPUS_DIR)) == 230


def test_corpus_known_method():
    chunks = split_corpus(CORPUS_DIR)
    found = [c for c in chunks if c.name == "SessionRedirectMixin.should_strip_auth"]
    assert len(found) == 1
    chunk = found[0]
    assert (chunk.file, chunk.start_line, chunk.end_line) == ("sessions.py", 127, 157)
    assert chunk.text.split("\n")[0].strip() == "def should_strip_auth(self, old_url, new_url):"


def test_corpus_order_is_by_file_then_line():
    chunks = split_corpus(CORPUS_DIR)
    keys = [(c.file, c.start_line) for c in chunks]
    assert keys == sorted(keys)
