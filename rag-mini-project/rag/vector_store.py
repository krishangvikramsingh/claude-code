"""FAISS-backed vector store with a persisted chunk table and manifest.

Index: IndexFlatIP over L2-normalised vectors (exact cosine similarity).
Files in index_dir: index.faiss, chunks.jsonl, manifest.json, embedder.joblib
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .chunking import Chunk
from .errors import IndexNotBuiltError, RetrievalError


class VectorStore:
    def __init__(self, index, chunks: list[Chunk], manifest: dict):
        self.index, self.chunks, self.manifest = index, chunks, manifest

    @classmethod
    def build(cls, vectors: np.ndarray, chunks: list[Chunk], manifest: dict) -> "VectorStore":
        import faiss

        if len(chunks) != len(vectors) or len(chunks) == 0:
            raise ValueError("vectors and chunks must be non-empty and the same length")
        idx = faiss.IndexFlatIP(vectors.shape[1])
        idx.add(np.ascontiguousarray(vectors, dtype=np.float32))
        manifest = {**manifest, "dim": int(vectors.shape[1]), "n_vectors": int(idx.ntotal),
                    "faiss_index": "IndexFlatIP", "metric": "cosine (inner product on L2-normalised vectors)"}
        return cls(idx, chunks, manifest)

    def save(self, directory: Path) -> None:
        import faiss

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "index.faiss"))
        with open(directory / "chunks.jsonl", "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        (directory / "manifest.json").write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path) -> "VectorStore":
        import faiss

        directory = Path(directory)
        need = ["index.faiss", "chunks.jsonl", "manifest.json"]
        if not all((directory / n).is_file() for n in need):
            raise IndexNotBuiltError("The index has not been built yet. Run the indexing step first.")
        try:
            index = faiss.read_index(str(directory / "index.faiss"))
            chunks = [Chunk(**json.loads(ln)) for ln in (directory / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if ln]
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        except Exception as e:
            raise IndexNotBuiltError(f"The stored index is corrupted ({type(e).__name__}). Rebuild it.") from e
        if index.ntotal != len(chunks):
            raise IndexNotBuiltError("Index and chunk table are out of sync. Rebuild the index.")
        return cls(index, chunks, manifest)

    def search(self, qvec: np.ndarray, k: int, doc_filter: set[str] | None = None) -> list[tuple[Chunk, float]]:
        """Top-k (chunk, cosine score). With a filter, score every vector (exact flat index) then post-filter."""
        if qvec.ndim == 1:
            qvec = qvec[None, :]
        if qvec.shape[1] != self.index.d:
            raise RetrievalError("Query vector dimension does not match the index (was the embedder changed?)")
        fetch = self.index.ntotal if doc_filter else min(self.index.ntotal, k)
        scores, ids = self.index.search(np.ascontiguousarray(qvec, dtype=np.float32), fetch)
        out = []
        for s, i in zip(scores[0], ids[0]):
            if i < 0:
                continue
            c = self.chunks[int(i)]
            if doc_filter and c.doc not in doc_filter:
                continue
            out.append((c, float(s)))
            if len(out) == k:
                break
        return out
