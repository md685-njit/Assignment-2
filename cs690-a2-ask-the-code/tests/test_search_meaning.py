"""Public tests for Step 7 (askcode/search_meaning.py). Run: pytest tests/test_search_meaning.py

These tests use tiny fake embedding functions, so they run without the real model.
"""

import math

import pytest

from askcode.core import Chunk
from askcode.search_meaning import MeaningIndex, cosine

TOPICS = ["redirect", "cookie", "proxy"]


def fake_vector(text: str) -> list[float]:
    lowered = text.lower()
    return [float(lowered.count(topic)) for topic in TOPICS]


class FakeModel:
    def __init__(self):
        self.passage_calls = []
        self.query_calls = []

    def passages(self, texts):
        self.passage_calls.append(list(texts))
        return [fake_vector(t) for t in texts]

    def query(self, text):
        self.query_calls.append(text)
        return fake_vector(text)


def chunk(name: str, text: str) -> Chunk:
    return Chunk(file="demo.py", name=name, start_line=1, end_line=1, text=text)


CHUNKS = [
    chunk("follow", "redirect redirect"),
    chunk("jar", "cookie"),
    chunk("route", "proxy proxy proxy"),
]


def test_cosine_values():
    assert cosine([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 3.0]) == pytest.approx(0.0)
    assert cosine([1.0, 1.0], [1.0, 0.0]) == pytest.approx(1 / math.sqrt(2))


def test_cosine_zero_vector_is_zero():
    assert cosine([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_cosine_length_mismatch():
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 2.0])


def test_chunks_are_embedded_once_with_name_and_text():
    model = FakeModel()
    MeaningIndex(CHUNKS, embed_passages=model.passages, embed_query=model.query)
    assert model.passage_calls == [["follow\nredirect redirect", "jar\ncookie", "route\nproxy proxy proxy"]]


def test_search_ranks_by_meaning_and_embeds_only_the_question():
    model = FakeModel()
    index = MeaningIndex(CHUNKS, embed_passages=model.passages, embed_query=model.query)
    result = index.search("which proxy is used", k=2)
    assert [c.name for c in result] == ["route", "follow"]
    assert model.query_calls == ["which proxy is used"]
    assert len(model.passage_calls) == 1


def test_search_always_returns_k():
    model = FakeModel()
    index = MeaningIndex(CHUNKS, embed_passages=model.passages, embed_query=model.query)
    assert len(index.search("nothing related at all", k=3)) == 3
