# VALIDATION CHECKLIST

Automated checks: `python source_code/src/validate_submission.py` → `results/validation_report.txt` (**23/23 passed** at the time of packaging); tests: `python -m pytest tests -q` → **43 passed** (`results/test_results.txt`).

## Technical verification
| Item | Status | Evidence |
|---|---|---|
| Original project inspected, inventory and audit written | ✅ | `documentation/PROJECT_AUDIT.md` |
| All transformations in the code identified and documented (no invented ones) | ✅ | `documentation/TRANSFORMATIONS_REFERENCE.md` (T1–T20) |
| Original experiment reproduced | ✅ | `results/tables/legacy_reproduction_cameraman.csv`, max \|ΔNC\| = 0.004 |
| Improved code executes; tests pass | ✅ | 43 passed |
| Dataset has 100 unique source images | ✅ | pixel-uniqueness test + validation report; 94 real + 6 labelled synthetic |
| Every image/transformation has a recorded status | ✅ | `results_attacks.csv` (3000 ok), `results_alpha_sweep.csv` (4000 ok), `results_controls.csv` (1600), `metadata.csv` status columns |
| Outputs re-opened and checked | ✅ | 100/100 watermarked PNGs valid (`results_images.csv`) |
| Results correspond to actual executions; charts use recorded results | ✅ | `analysis.py` reads CSVs only; report/deck built from CSV/JSON; two full runs identical |
| Video claims supported by video experiments | ✅ | `results/video_demo_results.csv` (720 decoded frames); labelled exploratory |
| Technology comparison separates measured from documentation-based | ✅ | `research/TECHNOLOGY_COMPARISON.md` §1 (documentation) vs §2–3 (measured) |

## Research verification
| Item | Status | Note |
|---|---|---|
| References traceable to real sources | ✅ / ⚠️ | 32 entries, each with status V1/V2/V3 in `research/REFERENCES.md`. **V1** (publisher-confirmed): [1], [8]*, [16], [17], [19]–[22]. **V2** (confirmed through secondary listings; DOI not confirmed): most others. **V3** (not independently verified: Golub & Van Loan, Gonzalez & Woods, Cox et al. book, author initials of [8][9]) — **check these before final submission**. |
| Substantial claims have citations; no invented papers | ✅ | unverifiable items left out (Rykaczewski 2007) |
| Original claims without sources flagged | ✅ | NC > 0.75, "30 dB / 0.98 SSIM" labelled as conventions |
| Report does not misrepresent the origin of the code | ✅ | §2 "foundational literature identified during this review" |

## Document verification
| Item | Status | Evidence |
|---|---|---|
| Report opens (python-docx, LibreOffice → PDF), contents/lists/page numbers consistent | ✅ | 37 pages, 0 unresolved entries |
| Figures legible, captions numbered per chapter | ✅ | visual inspection of every page sheet |
| Deck opens; 24 slides; speaker notes on all | ✅ | `validate_submission.py` |
| No placeholder text | ✅ | regex scan of report and deck |
| Report and deck agree on objectives, methods, headline numbers | ✅ | same data files; cross-checked 85.1 %, NC 0.975 |
| All required files present | ✅ | 29-file check |

## Unresolved issues / assumptions
1. **Word rendering not tested in Microsoft Word** — files were generated with python-docx and python-pptx and rendered/checked with LibreOffice (Calibri is substituted by Carlito in the PDFs).
2. **Canva not edited** (no link/existing design) — `presentation/CANVA_NOTES.md`.
3. **No university template** or supervisor details were supplied: none invented; the report uses a conventional structure.
4. Image rights: most photographs have no upstream licence statement (see `data/README.md`); the images are for academic evaluation only.
5. The false-positive problem is measured, not fixed.
6. V3 references (above) need a manual check.
7. Only one existing watermarking package was benchmarked; GPU variants and learned methods were not.
8. Timing results vary 5–10 % run to run; all other metrics are bit-reproducible.
