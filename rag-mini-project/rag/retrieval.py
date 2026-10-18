"""Query embedding + top-k similarity retrieval."""
from __future__ import annotations

from dataclasses import dataclass

from .chunking import Chunk
from .config import Settings
from .embeddings import load_embedder
from .errors import RetrievalError
from .vector_store import VectorStore


@dataclass
class Retrieved:
    rank: int
    score: float
    chunk: Chunk

    @property
    def label(self) -> str:
        return f"S{self.rank}"


class Retriever:
    def __init__(self, s: Settings):
        self.s = s
        self.store = VectorStore.load(s.index_dir)
        kind = self.store.manifest.get("embedder_kind", s.embedder)
        self.embedder = load_embedder(s.index_dir, kind, self.store.manifest.get("st_model", s.st_model))

    def retrieve(self, query: str, k: int | None = None, doc_filter: set[str] | None = None) -> list[Retrieved]:
        if not isinstance(query, str) or not query.strip():
            raise RetrievalError("Please enter a non-empty question.")
        k = k or self.s.top_k
        if k < 1:
            raise RetrievalError("top_k must be at least 1.")
        try:
            qv = self.embedder.encode([query.strip()])
            hits = self.store.search(qv, k, doc_filter)
        except RetrievalError:
            raise
        except Exception as e:
            raise RetrievalError(f"Retrieval failed ({type(e).__name__}).") from e
        return [Retrieved(i, sc, c) for i, (c, sc) in enumerate(hits, 1)]
