"""Embedding backends. All return L2-normalised float32 matrices so inner product == cosine.

* ``lsa``   : TF-IDF (1-2 grams) + TruncatedSVD, fitted on the corpus. Fully offline. (default)
* ``tfidf`` : TF-IDF vectors (dense, vocabulary-sized). Offline lexical baseline.
* ``sentence-transformers`` : pretrained neural model (needs the model download; optional dependency).
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .errors import RAGError


class Embedder(Protocol):
    name: str
    dim: int

    def fit(self, texts: list[str]) -> None: ...
    def encode(self, texts: list[str]) -> np.ndarray: ...
    def save(self, directory: Path) -> None: ...


def l2_normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (x / n).astype(np.float32)


class _SklearnEmbedder:
    def __init__(self, kind: str, dims: int = 128):
        self.kind, self.dims = kind, dims
        self.name = kind
        self.dim = 0
        self.vec = None
        self.svd = None

    def fit(self, texts: list[str]) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        if not texts:
            raise RAGError("Cannot fit embedder on an empty corpus")
        self.vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), stop_words="english",
                                   strip_accents="unicode", min_df=1)
        X = self.vec.fit_transform(texts)
        if self.kind == "lsa":
            k = max(2, min(self.dims, X.shape[0] - 1, X.shape[1] - 1))
            self.svd = TruncatedSVD(n_components=k, random_state=0)
            self.svd.fit(X)
            self.dim = k
        else:
            self.dim = X.shape[1]

    def encode(self, texts: list[str]) -> np.ndarray:
        if self.vec is None:
            raise RAGError("Embedder is not fitted")
        X = self.vec.transform(texts)
        if self.kind == "lsa":
            return l2_normalize(self.svd.transform(X))
        return l2_normalize(X.toarray())

    def save(self, directory: Path) -> None:
        import joblib

        joblib.dump({"kind": self.kind, "dims": self.dims, "vec": self.vec, "svd": self.svd, "dim": self.dim},
                    Path(directory) / "embedder.joblib")

    @classmethod
    def load(cls, directory: Path) -> "_SklearnEmbedder":
        import joblib

        d = joblib.load(Path(directory) / "embedder.joblib")  # trusted local artifact written by save()
        e = cls(d["kind"], d["dims"])
        e.vec, e.svd, e.dim = d["vec"], d["svd"], d["dim"]
        return e


class SentenceTransformerEmbedder:
    """Pretrained neural embeddings. Requires `pip install sentence-transformers` and model download."""

    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RAGError("sentence-transformers is not installed (see requirements-optional.txt)") from e
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:  # network / missing model
            raise RAGError(f"Could not load embedding model '{model_name}': {type(e).__name__}") from e
        self.model_name = model_name
        self.name = f"sentence-transformers:{model_name}"
        self.dim = int(self.model.get_sentence_embedding_dimension())

    def fit(self, texts: list[str]) -> None:  # pretrained: nothing to fit
        pass

    def encode(self, texts: list[str]) -> np.ndarray:
        return l2_normalize(self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True))

    def save(self, directory: Path) -> None:
        (Path(directory) / "embedder.txt").write_text(self.model_name, encoding="utf-8")


def make_embedder(kind: str, dims: int = 128, st_model: str = ""):
    if kind in ("lsa", "tfidf"):
        return _SklearnEmbedder(kind, dims)
    if kind == "sentence-transformers":
        return SentenceTransformerEmbedder(st_model)
    raise RAGError(f"Unknown embedder '{kind}' (choose lsa, tfidf, sentence-transformers)")


def load_embedder(directory: Path, kind: str, st_model: str = ""):
    if kind in ("lsa", "tfidf"):
        return _SklearnEmbedder.load(directory)
    return SentenceTransformerEmbedder(st_model)
