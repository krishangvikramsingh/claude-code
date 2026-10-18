"""CLI: (re)build the vector index.  Usage: python scripts/build_index.py [--chunk-size N] [--overlap N] [--embedder lsa|tfidf|sentence-transformers]"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag.config import Settings, load_dotenv_if_present  # noqa: E402
from rag.errors import RAGError  # noqa: E402
from rag.ingestion import build_index  # noqa: E402

if __name__ == "__main__":
    load_dotenv_if_present()
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-size", type=int)
    ap.add_argument("--overlap", type=int)
    ap.add_argument("--embedder")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.getLogger("faiss.loader").setLevel(logging.WARNING)
    s = Settings()
    kw = {k: v for k, v in dict(chunk_size=a.chunk_size, chunk_overlap=a.overlap, embedder=a.embedder).items() if v is not None}
    try:
        rep = build_index(s.with_(**kw))
    except RAGError as e:
        sys.exit(f"ERROR: {e}")
    print(json.dumps({k: v for k, v in rep.to_dict().items() if k != "files"}, indent=2))
    for f in rep.files:
        print(f"  {f.status:7} {f.file:40} segments={f.pages_or_segments:3} chunks={f.chunks:3} {f.message}")
