import json
import shutil

import numpy as np
import pytest

from rag.embeddings import l2_normalize, make_embedder
from rag.errors import IndexNotBuiltError, IngestionError, RAGError, RetrievalError
from rag.ingestion import build_index, index_is_stale, process_corpus
from rag.retrieval import Retriever
from rag.vector_store import VectorStore


def test_ingest_continues_past_bad_files(settings, tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(settings.kb_dir / "02_text_chunking.md", kb)
    (kb / "broken.pdf").write_bytes(b"garbage")
    (kb / "empty.txt").write_bytes(b"")
    (kb / "sheet.xlsx").write_bytes(b"x")
    s = settings.with_(kb_dir=kb, index_dir=tmp_path / "idx")
    rep = build_index(s)
    status = {f.file: f.status for f in rep.files}
    assert status["02_text_chunking.md"] == "ok"
    assert status["broken.pdf"] == status["empty.txt"] == status["sheet.xlsx"] == "failed"
    assert rep.n_ok == 1 and rep.n_failed == 3 and rep.total_chunks > 0
    assert all("Traceback" not in f.message for f in rep.files)


def test_no_usable_documents_raises(settings, tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "empty.txt").write_bytes(b"")
    with pytest.raises(IngestionError):
        build_index(settings.with_(kb_dir=kb, index_dir=tmp_path / "i"))


def test_missing_kb_dir(settings, tmp_path):
    with pytest.raises(IngestionError):
        build_index(settings.with_(kb_dir=tmp_path / "nope", index_dir=tmp_path / "i"))


def test_duplicate_chunks_removed(settings, tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(settings.kb_dir / "02_text_chunking.md", kb / "a.md")
    shutil.copy(settings.kb_dir / "02_text_chunking.md", kb / "b.md")
    chunks, _, dups = process_corpus(kb, settings)
    assert dups == len(chunks) > 0


def test_stale_detection_and_rebuild(settings, tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(settings.kb_dir / "02_text_chunking.md", kb / "a.md")
    s = settings.with_(kb_dir=kb, index_dir=tmp_path / "idx")
    assert index_is_stale(s)
    build_index(s)
    assert not index_is_stale(s)
    (kb / "new.md").write_text("# New\n\n## Topic\n\nA brand new fact about zebras and their stripes in the wild.\n", encoding="utf-8")
    assert index_is_stale(s)
    build_index(s)
    assert not index_is_stale(s)
    hits = Retriever(s).retrieve("zebras stripes", 1)
    assert hits[0].chunk.doc == "new.md"
    assert index_is_stale(s.with_(chunk_size=300))


def test_index_persistence_roundtrip(settings):
    store = VectorStore.load(settings.index_dir)
    m = json.loads((settings.index_dir / "manifest.json").read_text())
    assert store.index.ntotal == len(store.chunks) == m["n_chunks"]
    assert m["metric"].startswith("cosine") and m["dim"] == store.index.d


def test_vectors_are_unit_norm(settings):
    import faiss

    idx = faiss.read_index(str(settings.index_dir / "index.faiss"))
    v = idx.reconstruct_n(0, idx.ntotal)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-4)


def test_l2_normalize_zero_vector():
    out = l2_normalize(np.zeros((1, 4)))
    assert not np.isnan(out).any()


def test_embedder_dim_and_unit_norm():
    e = make_embedder("lsa", 8)
    texts = [f"document {i} about subject {i % 3} and word{i}" for i in range(20)]
    e.fit(texts)
    v = e.encode(["document about subject"])
    assert v.shape == (1, e.dim) and abs(np.linalg.norm(v) - 1) < 1e-5


def test_unknown_embedder_and_unfitted():
    with pytest.raises(RAGError):
        make_embedder("nope")
    with pytest.raises(RAGError):
        make_embedder("lsa").encode(["x"])


def test_load_missing_index(tmp_path):
    with pytest.raises(IndexNotBuiltError):
        VectorStore.load(tmp_path / "none")


def test_corrupted_index_reports_cleanly(settings, tmp_path):
    d = tmp_path / "idx"
    shutil.copytree(settings.index_dir, d)
    (d / "index.faiss").write_bytes(b"junk")
    with pytest.raises(IndexNotBuiltError):
        VectorStore.load(d)


# ---- retrieval ----
def test_empty_query_rejected(settings):
    r = Retriever(settings)
    for q in ("", "   ", None):
        with pytest.raises(RetrievalError):
            r.retrieve(q)


def test_invalid_k(settings):
    with pytest.raises(RetrievalError):
        Retriever(settings).retrieve("anything", k=-1)


@pytest.mark.parametrize("query,doc,phrase", [
    ("How many dimensions does all-MiniLM-L6-v2 produce?", "03_embeddings_and_similarity.docx", "384"),
    ("Which function saves a FAISS index to disk?", "04_vector_search_faiss.pdf", "write_index"),
    ("What does Precision@k measure?", "05_retrieval_metrics.md", "divided by k"),
])
def test_known_passage_is_top1(settings, query, doc, phrase):
    top = Retriever(settings).retrieve(query, 3)[0]
    assert top.chunk.doc == doc and phrase in top.chunk.text
    assert top.rank == 1 and 0 < top.score <= 1.0001


def test_scores_sorted_descending(settings):
    hits = Retriever(settings).retrieve("chunk overlap", 5)
    s = [h.score for h in hits]
    assert s == sorted(s, reverse=True) and len(hits) == 5


def test_doc_filter(settings):
    hits = Retriever(settings).retrieve("index", 3, doc_filter={"05_retrieval_metrics.md"})
    assert hits and all(h.chunk.doc == "05_retrieval_metrics.md" for h in hits)


def test_page_metadata_for_pdf_chunks(settings):
    hits = Retriever(settings).retrieve("write_index read_index persistence", 1)
    assert hits[0].chunk.doc.endswith(".pdf") and hits[0].chunk.page == 2


def test_dimension_mismatch_detected(settings):
    store = VectorStore.load(settings.index_dir)
    with pytest.raises(RetrievalError):
        store.search(np.ones((1, store.index.d + 3), dtype=np.float32), 2)
