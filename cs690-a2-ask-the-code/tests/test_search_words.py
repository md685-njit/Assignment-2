"""Public tests for Step 3 (askcode/search_words.py). Run: pytest tests/test_search_words.py"""

from askcode import CORPUS_DIR
from askcode.core import Chunk
from askcode.search_words import search_words
from askcode.split import split_corpus


def chunk(name: str, text: str) -> Chunk:
    return Chunk(file="demo.py", name=name, start_line=1, end_line=1, text=text)


CHUNKS = [
    chunk("open_session", "session = make_session()"),
    chunk("close_session", "session.close()"),
    chunk("digest_login", "session digest nonce"),
    chunk("render_page", "html template"),
]


def test_rare_word_outranks_common_word():
    # "digest" is in 1 chunk, "session" is in 3, so the digest chunk must come first.
    result = search_words("digest session", CHUNKS, k=4)
    assert [c.name for c in result] == ["digest_login", "open_session", "close_session"]


def test_chunks_with_no_shared_word_are_left_out():
    assert [c.name for c in search_words("template", CHUNKS, k=3)] == ["render_page"]


def test_at_most_k():
    assert len(search_words("session", CHUNKS, k=2)) == 2


def test_ties_keep_the_original_order():
    result = search_words("session", CHUNKS, k=3)
    assert [c.name for c in result] == ["open_session", "close_session", "digest_login"]


def test_only_stopwords_gives_nothing():
    assert search_words("what is the", CHUNKS, k=3) == []


def test_function_names_count_as_words():
    # "render" appears only in a chunk's name, not in its text.
    assert [c.name for c in search_words("render", CHUNKS, k=3)] == ["render_page"]


def test_corpus_redirect_question_finds_should_strip_auth_first():
    chunks = split_corpus(CORPUS_DIR)
    result = search_words("strip the Authorization header on redirect", chunks, k=3)
    assert result[0].name == "SessionRedirectMixin.should_strip_auth"
    assert len(result) == 3
