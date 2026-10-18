"""Knowledge-base ingestion: load -> clean -> chunk -> dedupe -> embed -> index -> persist."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .chunking import Chunk, chunk_segments, validate_chunks
from .config import Settings
from .document_loader import SUPPORTED, load_document
from .embeddings import load_embedder, make_embedder
from .errors import IngestionError, RAGError
from .text_cleaner import clean_segments
from .vector_store import VectorStore

log = logging.getLogger("rag.ingestion")


@dataclass
class FileReport:
    file: str
    status: str            # ok | failed | skipped
    pages_or_segments: int = 0
    chunks: int = 0
    chars: int = 0
    message: str = ""
    stats: dict = field(default_factory=dict)


@dataclass
class IngestReport:
    files: list[FileReport]
    total_chunks: int = 0
    duplicates_removed: int = 0
    seconds: float = 0.0
    embedder: str = ""
    dim: int = 0

    @property
    def n_ok(self) -> int:
        return sum(f.status == "ok" for f in self.files)

    @property
    def n_failed(self) -> int:
        return sum(f.status == "failed" for f in self.files)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(n_ok=self.n_ok, n_failed=self.n_failed)
        return d


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def kb_fingerprint(kb_dir: Path) -> dict[str, str]:
    return {p.name: file_sha256(p) for p in sorted(Path(kb_dir).iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED}


def process_corpus(kb_dir: Path, s: Settings) -> tuple[list[Chunk], list[FileReport], int]:
    """Load/clean/chunk every file. Failures are recorded per file and never abort the run."""
    kb_dir = Path(kb_dir)
    if not kb_dir.is_dir():
        raise IngestionError(f"Knowledge-base folder not found: {kb_dir.name}")
    reports, all_chunks = [], []
    for p in sorted(kb_dir.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        try:
            segs = load_document(p)
            segs, cstats = clean_segments(segs)
            chunks, kstats = chunk_segments(p.name, segs, s.chunk_size, s.chunk_overlap, s.min_chunk_chars)
            problems = validate_chunks(chunks, s.chunk_size)
            if problems:
                raise IngestionError(f"{p.name}: chunk validation failed: {problems[0]}")
            if not chunks:
                raise IngestionError(f"{p.name}: produced no chunks")
            all_chunks.extend(chunks)
            reports.append(FileReport(p.name, "ok", len(segs), len(chunks), cstats["chars_after"], "", {**cstats, **kstats}))
            log.info("ingested %s: %d segments, %d chunks", p.name, len(segs), len(chunks))
        except RAGError as e:
            reports.append(FileReport(p.name, "failed", message=str(e)))
            log.warning("failed %s: %s", p.name, e)
        except Exception as e:  # unexpected: record type only, no stack trace for the user
            reports.append(FileReport(p.name, "failed", message=f"{p.name}: unexpected error ({type(e).__name__})"))
            log.exception("unexpected error ingesting %s", p.name)
    # duplicate handling: identical (case-insensitive) chunk text keeps the first occurrence
    seen, unique = set(), []
    for c in all_chunks:
        if c.text_hash in seen:
            continue
        seen.add(c.text_hash)
        unique.append(c)
    return unique, reports, len(all_chunks) - len(unique)


def build_index(s: Settings) -> IngestReport:
    """Full (re)build of the persisted index from the knowledge-base folder."""
    s.validate()
    t0 = time.time()
    chunks, reports, dups = process_corpus(s.kb_dir, s)
    if not chunks:
        raise IngestionError("No usable chunks were produced; check the knowledge-base folder and the file report.")
    emb = make_embedder(s.embedder, s.lsa_dims, s.st_model)
    texts = [c.text for c in chunks]
    emb.fit(texts)
    vectors = emb.encode(texts)
    manifest = {
        "embedder": emb.name, "chunk_size": s.chunk_size, "chunk_overlap": s.chunk_overlap,
        "files": kb_fingerprint(s.kb_dir), "n_chunks": len(chunks), "duplicates_removed": dups,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"), "embedder_kind": s.embedder, "st_model": s.st_model,
    }
    store = VectorStore.build(vectors, chunks, manifest)
    store.save(s.index_dir)
    emb.save(s.index_dir)
    (Path(s.index_dir) / "ingest_report.json").write_text(
        json.dumps(IngestReport(reports, len(chunks), dups, time.time() - t0, emb.name, emb.dim).to_dict(), indent=2), encoding="utf-8")
    rep = IngestReport(reports, len(chunks), dups, round(time.time() - t0, 3), emb.name, emb.dim)
    log.info("index built: %d chunks, dim=%d, %d dup removed", len(chunks), emb.dim, dups)
    return rep


def index_is_stale(s: Settings) -> bool:
    """True if the index is missing or the KB files / chunk settings changed since it was built."""
    mf = Path(s.index_dir) / "manifest.json"
    if not mf.is_file():
        return True
    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
        return (m.get("files") != kb_fingerprint(s.kb_dir) or m.get("chunk_size") != s.chunk_size
                or m.get("chunk_overlap") != s.chunk_overlap or m.get("embedder_kind") != s.embedder)
    except Exception:
        return True


def load_report(s: Settings) -> dict | None:
    p = Path(s.index_dir) / "ingest_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


__all__ = ["build_index", "index_is_stale", "process_corpus", "load_report", "IngestReport", "FileReport", "load_embedder"]
