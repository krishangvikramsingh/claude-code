"""Central configuration. Values come from defaults, overridable by environment variables.

No secrets are stored here; API keys are read from the environment only when needed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    kb_dir: Path = field(default_factory=lambda: Path(_env("RAG_KB_DIR", str(ROOT / "data" / "knowledge_base"))))
    index_dir: Path = field(default_factory=lambda: Path(_env("RAG_INDEX_DIR", str(ROOT / "artifacts" / "index"))))
    chunk_size: int = field(default_factory=lambda: int(_env("RAG_CHUNK_SIZE", "500")))       # characters
    chunk_overlap: int = field(default_factory=lambda: int(_env("RAG_CHUNK_OVERLAP", "100")))  # characters
    min_chunk_chars: int = field(default_factory=lambda: int(_env("RAG_MIN_CHUNK_CHARS", "40")))
    embedder: str = field(default_factory=lambda: _env("RAG_EMBEDDER", "lsa"))  # lsa | tfidf | sentence-transformers
    st_model: str = field(default_factory=lambda: _env("RAG_ST_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    lsa_dims: int = field(default_factory=lambda: int(_env("RAG_LSA_DIMS", "128")))
    top_k: int = field(default_factory=lambda: int(_env("RAG_TOP_K", "4")))
    min_score: float = field(default_factory=lambda: float(_env("RAG_MIN_SCORE", "0.15")))  # abstention threshold
    min_coverage: float = field(default_factory=lambda: float(_env("RAG_MIN_COVERAGE", "0.34")))  # extractive abstention
    llm_provider: str = field(default_factory=lambda: _env("RAG_LLM_PROVIDER", "extractive"))  # extractive | anthropic | ollama
    anthropic_model: str = field(default_factory=lambda: _env("RAG_ANTHROPIC_MODEL", "claude-haiku-5-5"))
    ollama_model: str = field(default_factory=lambda: _env("RAG_OLLAMA_MODEL", "llama3.1"))
    ollama_url: str = field(default_factory=lambda: _env("RAG_OLLAMA_URL", "http://localhost:11434"))
    max_context_chars: int = field(default_factory=lambda: int(_env("RAG_MAX_CONTEXT_CHARS", "6000")))

    def with_(self, **kw) -> "Settings":
        return replace(self, **kw)

    def validate(self) -> None:
        if self.chunk_size < 100:
            raise ValueError("chunk_size must be >= 100 characters")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("chunk_overlap must satisfy 0 <= overlap < chunk_size")
        if self.top_k < 1:
            raise ValueError("top_k must be >= 1")


def load_dotenv_if_present(path: Path | None = None) -> None:
    """Minimal .env reader (KEY=VALUE lines) so python-dotenv is not required."""
    p = path or ROOT / ".env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
