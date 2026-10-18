"""Reproducible evaluation: retrieval metrics, answer correctness, grounding, abstention, injection checks.

Relevance labels: a retrieved chunk is RELEVANT iff its document is in the case's evidence docs and its text
contains the evidence phrase (case-insensitive). All judgments are rule-based and deterministic; no LLM judge.

Metrics (answerable cases only):
  Precision@k = |relevant chunks in top-k| / k
  Recall@k    = |evidence items covered by top-k| / |evidence items|   (an evidence item = one doc+phrase)
  RR          = 1 / rank of first relevant chunk (0 if none); MRR = mean RR
  Hit@k       = 1 if any relevant chunk in top-k
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .generation import content_terms
from .rag_pipeline import RAGAnswer, RAGPipeline


def load_cases(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["cases"]


def chunk_matches(chunk, ev: dict) -> bool:
    return chunk.doc == ev["doc"] and ev["phrase"].lower() in chunk.text.lower()


def retrieval_metrics(retrieved, evidence: list[dict], k: int) -> dict:
    top = retrieved[:k]
    rel_flags = [any(chunk_matches(r.chunk, e) for e in evidence) for r in top]
    covered = sum(any(chunk_matches(r.chunk, e) for r in top) for e in evidence)
    first = next((i for i, f in enumerate(rel_flags, 1) if f), None)
    return {"precision_at_k": sum(rel_flags) / k if k else 0.0, "recall_at_k": covered / len(evidence),
            "rr": 1 / first if first else 0.0, "hit_at_k": float(first is not None), "relevant_ranks": [i for i, f in enumerate(rel_flags, 1) if f]}


def _answer_sentences(text: str) -> list[str]:
    body = re.sub(r"\[S\d+\]", "", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.split()) >= 3]


def faithfulness(ans: RAGAnswer) -> float:
    """Mean over answer sentences of the share of their content terms found in the cited passages.
    A lexical-overlap proxy, NOT a semantic entailment check (see report limitations)."""
    if ans.abstained:
        return 1.0
    cited = [r for r in ans.retrieved if r.label in ans.cited]
    if not cited:
        return 0.0
    support = set().union(*(content_terms(r.chunk.text) for r in cited))
    sents = _answer_sentences(ans.answer)
    if not sents:
        return 0.0
    vals = []
    for s in sents:
        t = content_terms(s)
        vals.append(len(t & support) / len(t) if t else 1.0)
    return sum(vals) / len(vals)


def citations_valid(ans: RAGAnswer) -> bool:
    labels = {r.label for r in ans.retrieved}
    found = set(re.findall(r"\[(S\d+)\]", ans.answer))
    return found <= labels and (ans.abstained or bool(found))


def judge_case(case: dict, ans: RAGAnswer, k: int) -> dict:
    ev = case["evidence"]
    res = {"id": case["id"], "category": case["category"], "query": case["query"],
           "relevant_docs": case["relevant_docs"], "expected": case["reference_answer"],
           "retrieved": [f"{s['doc']}" + (f" p.{s['page']}" if s["page"] else "") + f" ({s['score']})" for s in ans.sources()],
           "answer": ans.answer, "abstained": ans.abstained}
    why: list[str] = []
    low = ans.answer.lower()
    # retrieval
    if ev and case["expected_behavior"] not in ("abstain_or_relevant",):
        m = retrieval_metrics(ans.retrieved, ev, k)
        res.update({k_: m[k_] for k_ in ("precision_at_k", "recall_at_k", "rr", "hit_at_k")})
        res["retrieval"] = "relevant chunk retrieved" if m["hit_at_k"] else "MISS"
        if not m["hit_at_k"]:
            why.append("retrieval miss: no relevant chunk in top-k")
    else:
        res["retrieval"] = "n/a"
    # grounding
    f = faithfulness(ans)
    res["faithfulness"] = round(f, 3)
    grounded = citations_valid(ans) and f >= 0.8
    res["grounding"] = "grounded" if grounded else "NOT grounded"
    if not grounded:
        why.append(f"grounding failed (citations_valid={citations_valid(ans)}, faithfulness={f:.2f})")
    leaked = [x for x in case["forbidden"] if x.lower() in low]
    if leaked:
        why.append(f"forbidden content in answer: {leaked}")
    # correctness / behavior
    eb = case["expected_behavior"]
    if eb == "answer":
        missing = [g for g in case["answer_must"] if not any(a.lower() in low for a in g)]
        correct = (not ans.abstained) and not missing
        if ans.abstained:
            why.append("abstained on an answerable question")
        elif missing:
            why.append(f"answer lacks expected facts: {[g[0] for g in missing]}")
    elif eb == "abstain":
        correct = ans.abstained
        if not correct:
            why.append("should have abstained but produced an answer")
    elif eb == "abstain_or_relevant":
        cited_docs = {r.chunk.doc for r in ans.retrieved if r.label in ans.cited}
        correct = ans.abstained or (bool(cited_docs) and cited_docs <= set(case["relevant_docs"]))
        if not correct:
            why.append("ambiguous query answered from unrelated documents")
    else:  # no_leak: answer a safe part (if any must-facts) without leaking/obeying
        missing = [g for g in case["answer_must"] if not any(a.lower() in low for a in g)]
        correct = not leaked and not missing
        if missing:
            why.append(f"answer lacks expected facts: {[g[0] for g in missing]}")
    if leaked:
        correct = False
    res["correct"] = "correct" if correct else "INCORRECT"
    passed = correct and (grounded or ans.abstained)
    res["pass"] = bool(passed)
    res["failure_explanation"] = "; ".join(why) if not passed else ""
    return res


@dataclass
class EvalSummary:
    n: int
    passed: int
    by_category: dict
    retrieval: dict
    abstention: dict
    config: dict = field(default_factory=dict)


def summarize(results: list[dict], cases: list[dict], config: dict) -> EvalSummary:
    cats: dict[str, list[dict]] = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)
    by_cat = {c: {"n": len(v), "passed": sum(x["pass"] for x in v)} for c, v in cats.items()}
    rr = [r for r in results if "precision_at_k" in r]
    n = len(rr) or 1
    retrieval = {"n_cases": len(rr), "precision_at_k": round(sum(r["precision_at_k"] for r in rr) / n, 4),
                 "recall_at_k": round(sum(r["recall_at_k"] for r in rr) / n, 4),
                 "mrr": round(sum(r["rr"] for r in rr) / n, 4), "hit_at_k": round(sum(r["hit_at_k"] for r in rr) / n, 4)}
    by_id = {c["id"]: c for c in cases}
    unans = [r for r in results if by_id[r["id"]]["expected_behavior"] == "abstain"]
    ans = [r for r in results if by_id[r["id"]]["expected_behavior"] == "answer"]
    abst = {"unanswerable_cases": len(unans), "correctly_abstained": sum(r["abstained"] for r in unans),
            "answerable_cases": len(ans), "wrongly_abstained": sum(r["abstained"] for r in ans)}
    return EvalSummary(len(results), sum(r["pass"] for r in results), by_cat, retrieval, abst, config)


def run_evaluation(pipe: RAGPipeline, cases: list[dict], k: int | None = None) -> tuple[list[dict], EvalSummary]:
    k = k or pipe.s.top_k
    results = [judge_case(c, pipe.ask(c["query"], k=k), k) for c in cases]
    cfg = {"chunk_size": pipe.s.chunk_size, "chunk_overlap": pipe.s.chunk_overlap, "top_k": k,
           "embedder": pipe.retriever.store.manifest.get("embedder"), "dim": pipe.retriever.store.manifest.get("dim"),
           "llm_provider": pipe.generator.name, "n_chunks": pipe.retriever.store.manifest.get("n_chunks"),
           "min_score": pipe.s.min_score, "min_coverage": pipe.s.min_coverage}
    return results, summarize(results, cases, cfg)


def write_outputs(results: list[dict], summary: EvalSummary, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "eval_results.json").write_text(json.dumps({"summary": summary.__dict__, "results": results}, indent=2), encoding="utf-8")
    cols = ["id", "category", "query", "expected", "retrieved", "answer", "retrieval", "correct", "grounding", "pass", "failure_explanation"]
    with open(out_dir / "eval_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({**r, "retrieved": " | ".join(r["retrieved"])})
