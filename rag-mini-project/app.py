"""Streamlit UI for the RAG mini project.  Run: streamlit run app.py"""
from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from rag.config import Settings, load_dotenv_if_present
from rag.document_loader import SUPPORTED
from rag.errors import RAGError
from rag.ingestion import build_index, index_is_stale, load_report
from rag.rag_pipeline import RAGPipeline

load_dotenv_if_present()
logging.getLogger("faiss").setLevel(logging.WARNING)
MAX_UPLOAD_MB = 10

st.set_page_config(page_title="RAG Mini Project", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner=False)
def get_pipeline(index_stamp: float, provider: str) -> RAGPipeline:
    return RAGPipeline(Settings().with_(llm_provider=provider))


def index_stamp(s: Settings) -> float:
    m = Path(s.index_dir) / "manifest.json"
    return m.stat().st_mtime if m.is_file() else 0.0


def rebuild(s: Settings) -> None:
    with st.spinner("Building index..."):
        try:
            rep = build_index(s)
            st.session_state["flash"] = ("success", f"Index built: {rep.n_ok} files ok, {rep.n_failed} failed, {rep.total_chunks} chunks.")
        except RAGError as e:
            st.session_state["flash"] = ("error", str(e))
    get_pipeline.clear()
    st.rerun()


s = Settings()
st.title("📚 Retrieval-Augmented Generation — Study-Guide Assistant")
st.caption("Answers are retrieved from a small SYNTHETIC knowledge base (original sample documents). "
           "Every answer cites retrieved passages; unsupported questions are refused.")
if "flash" in st.session_state:
    kind, msg = st.session_state.pop("flash")
    getattr(st, kind)(msg)

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("Index status")
    stamp = index_stamp(s)
    if stamp == 0.0:
        st.error("Index not built yet.")
    else:
        pipe0 = get_pipeline(stamp, "extractive")
        m = pipe0.retriever.store.manifest
        st.success("Index loaded")
        st.write(f"**Files:** {len(m['files'])}  \n**Chunks:** {m['n_chunks']}  \n**Embedder:** {m['embedder']} (dim {m['dim']})  \n"
                 f"**Chunking:** {m['chunk_size']} chars / {m['chunk_overlap']} overlap  \n**Built:** {m['built_at']}")
        if index_is_stale(s):
            st.warning("Knowledge-base files or chunk settings changed since the index was built. Rebuild to apply.")
    if st.button("Rebuild index", help="Re-reads data/knowledge_base and rebuilds the FAISS index"):
        rebuild(s)
    st.divider()
    st.header("Retrieval & generation")
    top_k = st.slider("Top-k passages", 1, 10, s.top_k)
    provider = st.selectbox("Answer generator", ["extractive", "anthropic", "ollama"],
                            help="extractive = offline, no LLM. anthropic needs ANTHROPIC_API_KEY. ollama needs a local server.")
    docs = sorted(get_pipeline(stamp, "extractive").retriever.store.manifest["files"]) if stamp else []
    doc_filter = st.multiselect("Restrict to documents", docs)
    st.divider()
    st.header("Add documents")
    ups = st.file_uploader("Upload PDF / DOCX / MD / TXT", type=[e.lstrip(".") for e in sorted(SUPPORTED)], accept_multiple_files=True)
    if ups and st.button("Save to knowledge base and re-index"):
        s.kb_dir.mkdir(parents=True, exist_ok=True)
        for u in ups:
            name = Path(u.name).name  # strip any path components
            if u.size > MAX_UPLOAD_MB * 1024 * 1024:
                st.error(f"{name}: larger than {MAX_UPLOAD_MB} MB, skipped")
                continue
            (s.kb_dir / name).write_bytes(u.getvalue())
        rebuild(s)

tab_ask, tab_kb = st.tabs(["Ask a question", "Knowledge base & ingestion diagnostics"])

with tab_ask:
    with st.form("q"):
        question = st.text_input("Your question", placeholder="e.g. How many dimensions does all-MiniLM-L6-v2 produce?")
        go = st.form_submit_button("Ask")
    if go:
        if stamp == 0.0:
            st.error("Build the index first (sidebar).")
        else:
            try:
                ans = get_pipeline(stamp, provider).ask(question, k=top_k, doc_filter=set(doc_filter) or None)
            except RAGError as e:
                st.error(str(e))
            else:
                if ans.abstained:
                    st.warning(ans.answer + " (The retrieved passages do not support an answer.)")
                else:
                    st.subheader("Answer")
                    st.write(ans.answer)
                st.caption(f"Generator: {ans.provider}")
                st.subheader("Retrieved passages" if ans.abstained else "Sources")
                rows = [{"Label": x["label"], "Document": x["doc"], "Page": x["page"] or "—", "Section": x["section"] or "—",
                         "Similarity": x["score"], "Cited in answer": "yes" if x["cited"] else "no"} for x in ans.sources()]
                st.dataframe(rows, hide_index=True, width="stretch")
                for r in ans.retrieved:
                    where = f"{r.chunk.doc}" + (f", page {r.chunk.page}" if r.chunk.page else "")
                    with st.expander(f"[{r.label}] {where} — similarity {r.score:.3f}"):
                        st.text(r.chunk.text)
                        st.caption(f"chunk id: {r.chunk.chunk_id} · section: {r.chunk.section or '—'}")
                with st.expander("Retrieval / generation diagnostics"):
                    st.json(ans.diagnostics)

with tab_kb:
    rep = load_report(s)
    if not rep:
        st.info("No ingestion report yet. Build the index.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Files OK", rep["n_ok"])
        c2.metric("Files failed", rep["n_failed"])
        c3.metric("Chunks indexed", rep["total_chunks"])
        c4.metric("Duplicates removed", rep["duplicates_removed"])
        st.dataframe([{"File": f["file"], "Status": f["status"], "Segments/pages": f["pages_or_segments"], "Chunks": f["chunks"],
                       "Chars": f["chars"], "Message": f["message"]} for f in rep["files"]], hide_index=True, width="stretch")
