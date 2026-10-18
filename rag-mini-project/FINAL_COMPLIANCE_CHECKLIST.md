# Final compliance checklist

Status legend: **DONE** = verified by inspecting the file or running the command shown; **PARTIAL** = delivered with a stated limitation; **PLACEHOLDER** = needs the team's input.
Guideline note: `coursera project.docx` could not be found (workspace / Google Drive); requirements below come from the task prompt's seven components.

## A. The seven components
| # | Component (limit) | Deliverable | Verification evidence | Status |
|---|---|---|---|---|
| 1 | Project Report (≤ 15 pp) | `docs/project_report.docx` (+ `docs/pdf/`) | LibreOffice PDF export: **8 pages** (`artifacts/page_counts.json`); contains title page, abstract, intro/problem/objectives/scope, architecture diagram (Fig. 1), stack, methodology, dataset, processing + diagram (Fig. 2), embedding/vector DB, LLM/prompt, UI + 2 real screenshots (Figs. 3-4), testing + results, discussion, limitations, future work, conclusion, references; page numbers in footer | DONE (title-page names/roll numbers are PLACEHOLDERS) |
| 2 | Dataset / KB (≤ 2 pp) | `docs/dataset_knowledge_base.docx` | **1 page**; actual counts: 9 files processed, 45 chunks, 14,198 chars; synthetic status stated; no URLs/dates because nothing was downloaded | DONE |
| 3 | Document Processing Module (one detailed diagram) | `docs/document_processing_module.docx`, `diagrams/document_processing_pipeline.png` + `.mmd` | 3 pages; exactly **1 image** in the DOCX (checked with python-docx); diagram matches `rag/ingestion.py` stages; also embedded in the report | DONE |
| 4 | Embedding & Vector DB (≤ 2 pp) | `docs/embedding_vector_database.docx` | **2 pages**; dimension 44 read from `artifacts/index/manifest.json`; experiment table from `artifacts/experiments/results.json` | DONE (neural model not executed: see §C) |
| 5 | LLM & Prompt Engineering (≤ 2 pp) | `docs/llm_prompt_engineering.docx` | **2 pages**; prompt text imported from `rag/prompt_templates.py` at build time | DONE (LLM providers not executed: see §C) |
| 6 | Testing & Evaluation (≤ 3 pp) | `docs/testing_evaluation.docx`; data in `data/evaluation/`, `artifacts/evaluation/` | **3 pages**; all 34 cases tabulated; metrics, failures and limits | DONE |
| 7 | Source code + README | `rag/`, `app.py`, `scripts/`, `tests/`, `README.md`, `requirements*.txt`, `.env.example`, `.gitignore`, `data/`, `diagrams/` | Clean-venv test: `pip install -r requirements.txt` → build index → **75 passed** → evaluation 29/34 → `start_app.sh` returned HTTP 200 → `stop_app.sh` stopped it | DONE |

## B. Functional requirements
| Requirement | Evidence | Status |
|---|---|---|
| Genuine retrieval over the KB (no hard-coded answers) | `rag/retrieval.py` + FAISS; tests `test_known_passage_is_top1`, `test_pipeline_answer_has_verifiable_sources`, and the new-document test in `test_stale_detection_and_rebuild` (a newly added file becomes retrievable) | DONE |
| Verifiable source references (file, page, section, score, text) | UI Sources table + `RAGAnswer.sources()`; test checks the cited chunk contains the claim; PDF page numbers tested | DONE |
| Unanswerable questions handled | 7/7 unanswerable/injection-only cases refused (`artifacts/evaluation/eval_results.csv`); **but** 4/24 answerable cases wrongly refused | DONE / PARTIAL (conservative) |
| Prompt-injection handling | system rules, escaping, delimiter tests, fixture `09_index_maintenance_note.txt`, injection queries | PARTIAL: only the extractive generator was run; LLM resistance untested |
| Empty/unsupported/corrupted files, empty query, retrieval failure | `tests/test_document_processing.py`, `tests/test_ingestion_index.py` | DONE |
| Configurable chunk size/overlap, embedder, top-k, provider | `rag/config.py`, `.env.example`, UI controls | DONE |
| Persistent index + reproducible re-index; KB updates | `artifacts/index`, manifest hashes, `scripts/build_index.py`, UI rebuild/upload | DONE |
| UI connected to real backend; index status; diagnostics | `app.py`; screenshots in `docs/screenshots/` are real captures of the running app | DONE |
| Evaluation: 8 question types; Precision@k, Recall@k, MRR; correctness, grounding, abstention | `data/evaluation/eval_set.json` (34 cases), `rag/evaluation.py`, `artifacts/evaluation/` | DONE (rule-based, small set) |
| Chunk-size / top-k comparison with recorded outputs | `artifacts/experiments/results.{json,md}` (18 configurations); no superiority claimed | DONE |

## C. Things that could NOT be done or verified (be transparent)
* `coursera project.docx` was not available → requirements taken from the prompt.
* sentence-transformers (all-MiniLM-L6-v2) embeddings: HuggingFace unreachable → implemented, **not executed**; the 384-dimension figure is the model's documented size, not verified here.
* Anthropic / Ollama generation: no API key or server → implemented, **not executed**; no LLM correctness/citation/injection results exist.
* No public corpus could be downloaded → knowledge base is **synthetic**, written by the AI assistant; the team should review it.
* References were written from memory (no web access) and must be re-checked.
* Page counts were measured with LibreOffice, not Microsoft Word.
* Mermaid `.mmd` files are not rendered by any script (PNGs come from matplotlib).
* Fabrication check: all metrics in the documents are generated from `artifacts/*.json` by `scripts/build_docs.py`.

## D. Packaging and hygiene
| Check | Evidence | Status |
|---|---|---|
| ZIP named `Coursera_Rollno1_Rollno2_Rollno3.zip` | `scripts/package_submission.py` (reads `docs/team_info.json`) | PLACEHOLDER roll numbers |
| ZIP contains all seven components in numbered folders | listing printed by the packager; archive tested with `zipfile.testzip()` | DONE |
| No secrets | regex scan in the packager (`sk-ant-…`, AWS, GitHub tokens) + `.env` excluded; `.env.example` has placeholders only | DONE |
| No venv, caches, generated index, model binaries | packager exclusions (`.venv`, `__pycache__`, `artifacts/index`, `.pytest_cache`) | DONE |

## E. Fields that still need the team's input
Roll numbers (currently `Rollno1`, `Rollno2`, `Rollno3`), student names, institution, supervisor, date → edit `docs/team_info.json`, then run `python scripts/build_docs.py && python scripts/check_pages.py && python scripts/package_submission.py`.
