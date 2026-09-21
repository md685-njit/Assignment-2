"""Turn text into vectors with a small embedding model that runs on your laptop.

GIVEN CODE. Do not change it.

Model: BAAI/bge-small-en-v1.5 (MIT license, 384 numbers per text), run with the
fastembed library. It is free and needs no API key. The first call downloads the
model once, about 67 MB, into the .models folder, which git ignores.
"""

from __future__ import annotations

from askcode import MODELS_DIR

MODEL_NAME = "BAAI/bge-small-en-v1.5"

# The bge v1.5 model card recommends this prefix on short queries that search for
# longer passages, which is exactly our case: a question searching for functions.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model = None


def _load_model():
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError(
                "fastembed is not installed. Activate your virtual environment and run: "
                "pip install -r requirements.txt"
            ) from exc
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        _model = TextEmbedding(model_name=MODEL_NAME, cache_dir=str(MODELS_DIR))
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """One vector per text, in the same order. Use this for chunks."""
    model = _load_model()
    return [vector.tolist() for vector in model.passage_embed(list(texts))]


def embed_query(text: str) -> list[float]:
    """One vector for a question. Adds the model's recommended query prefix."""
    model = _load_model()
    return next(iter(model.query_embed(QUERY_PREFIX + text))).tolist()
