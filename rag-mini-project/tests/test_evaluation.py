import json
from pathlib import Path

from rag.chunking import Chunk
from rag.evaluation import chunk_matches, faithfulness, judge_case, load_cases, retrieval_metrics, summarize
from rag.rag_pipeline import RAGAnswer
from rag.retrieval import Retrieved

ROOT = Path(__file__).resolve().parent.parent
CASES = load_cases(ROOT / "data" / "evaluation" / "eval_set.json")


def R(rank, doc, text):
    return Retrieved(rank, 0.5, Chunk(f"{doc}::{rank}", doc, None, None, text, len(text), "h"))


def test_metric_math_matches_worked_example():
    # 5 retrieved, relevant at ranks 3 and 5; 4 evidence items, 2 covered -> P@5 = 0.4, R@5 = 0.5, RR = 1/3
    ev = [{"doc": "a", "phrase": f"p{i}"} for i in range(4)]
    texts = ["x", "y", "p0 here", "z", "p1 here"]
    ret = [R(i + 1, "a", t) for i, t in enumerate(texts)]
    m = retrieval_metrics(ret, ev, 5)
    assert m["precision_at_k"] == 0.4 and m["recall_at_k"] == 0.5 and abs(m["rr"] - 1 / 3) < 1e-9 and m["relevant_ranks"] == [3, 5]


def test_metrics_no_relevant():
    m = retrieval_metrics([R(1, "a", "nothing")], [{"doc": "a", "phrase": "zzz"}], 1)
    assert m["rr"] == 0 and m["hit_at_k"] == 0 and m["precision_at_k"] == 0


def test_chunk_matches_requires_doc_and_phrase():
    c = Chunk("i", "a.md", None, None, "Has THE phrase", 14, "h")
    assert chunk_matches(c, {"doc": "a.md", "phrase": "the phrase"})
    assert not chunk_matches(c, {"doc": "b.md", "phrase": "the phrase"})


def test_faithfulness_penalises_unsupported_claims():
    ret = [R(1, "a", "Cats are small mammals that purr.")]
    good = RAGAnswer("q", "Cats are small mammals. [S1]", False, ["S1"], ret, "x")
    bad = RAGAnswer("q", "Quantum chromodynamics governs hadron confinement. [S1]", False, ["S1"], ret, "x")
    assert faithfulness(good) > 0.9 and faithfulness(bad) < 0.3
    assert faithfulness(RAGAnswer("q", "I could not find this in the knowledge base.", True, [], ret, "x")) == 1.0


def test_judge_flags_fabricated_citation():
    case = next(c for c in CASES if c["id"] == "A01")
    ans = RAGAnswer(case["query"], "It has 384 dimensions [S9].", False, [], [R(1, "03_embeddings_and_similarity.docx", "384-dimensional")], "x")
    r = judge_case(case, ans, 1)
    assert not r["pass"] and "grounding" in r["failure_explanation"]


def test_eval_set_well_formed():
    cats = {c["category"] for c in CASES}
    assert cats == {"direct_factual", "multi_passage", "paraphrase", "hard_retrieval", "unanswerable", "ambiguous", "misleading_wording", "prompt_injection"}
    assert len({c["id"] for c in CASES}) == len(CASES)
    assert all(c["reference_answer"] for c in CASES)


def test_every_evidence_phrase_exists_in_indexed_corpus(settings):
    """Guards the relevance labels: each gold evidence phrase must be present in some indexed chunk."""
    chunks = [json.loads(l) for l in (settings.index_dir / "chunks.jsonl").read_text().splitlines()]
    for c in CASES:
        for e in c["evidence"]:
            assert any(ch["doc"] == e["doc"] and e["phrase"].lower() in ch["text"].lower() for ch in chunks), (c["id"], e)


def test_summarize_counts():
    res = [{"id": "A01", "category": "direct_factual", "pass": True, "abstained": False, "precision_at_k": 1, "recall_at_k": 1, "rr": 1, "hit_at_k": 1},
           {"id": "E01", "category": "unanswerable", "pass": True, "abstained": True}]
    s = summarize(res, CASES, {})
    assert s.n == 2 and s.passed == 2 and s.abstention["correctly_abstained"] == 1 and s.retrieval["mrr"] == 1
