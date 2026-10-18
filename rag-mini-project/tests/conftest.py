import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.getLogger("faiss").setLevel(logging.WARNING)

from rag.config import Settings  # noqa: E402
from rag.ingestion import build_index  # noqa: E402
from rag.rag_pipeline import RAGPipeline  # noqa: E402


@pytest.fixture(scope="session")
def settings(tmp_path_factory) -> Settings:
    """Default settings pointing at the real sample KB, with a scratch index directory."""
    s = Settings().with_(index_dir=tmp_path_factory.mktemp("index"), kb_dir=ROOT / "data" / "knowledge_base",
                         chunk_size=500, chunk_overlap=100, embedder="lsa", top_k=4)
    build_index(s)
    return s


@pytest.fixture(scope="session")
def pipeline(settings) -> RAGPipeline:
    return RAGPipeline(settings)
