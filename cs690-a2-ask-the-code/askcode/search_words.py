"""Step 3: find the chunks that share the most useful words with the question.

YOUR CODE. Read HANDOUT.md, Step 3, first.
Check your work with:  pytest tests/test_search_words.py
"""

from __future__ import annotations

import math  # noqa: F401  (you will need it)

from askcode.core import STOPWORDS, Chunk, words  # noqa: F401


def search_words(question: str, chunks: list[Chunk], k: int = 3) -> list[Chunk]:
    """Return up to k chunks that best match the question by shared words.

    Scoring. The tests check the exact order this produces.

    1. Question words: the set of words(question), minus STOPWORDS.
    2. Chunk words: for each chunk, the set of words(chunk.name + "\\n" + chunk.text).
    3. For each question word w, df(w) is the number of chunks whose word set
       contains w, and N is len(chunks). Ignore question words no chunk contains.
    4. weight(w) = math.log(N / df(w)). A rare word weighs a lot; a word found in
       every chunk weighs 0.
    5. score(chunk) = the sum of weight(w) over the question words the chunk contains,
       rounded with round(score, 6). Rounding makes chunks that match the same words
       tie exactly, whatever order your code adds the weights in.
    6. Return the chunks whose score is greater than 0, highest score first, at most k
       of them. When two chunks have the same score, the one that comes first in
       `chunks` comes first.

    If the question has no words left after step 1, or chunks is empty, return [].

    This is the core idea of BM25, the standard keyword search (slide 45). BM25 adds
    adjustments for how often a word repeats and for chunk length.
    """
    raise NotImplementedError("Step 3: write search_words in askcode/search_words.py")
