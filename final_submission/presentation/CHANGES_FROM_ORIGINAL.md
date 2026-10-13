# Presentation: slide-by-slide changes

Original: 15 slides (`Original_Presentation.pptx`, navy/teal design, no speaker notes). Improved: 24 slides (`Final_Presentation.pptx`, PDF export `Final_Presentation.pdf`, speaker notes on every slide in the file and in `SPEAKER_NOTES.md`).
Design language kept: Calibri, navy `#132347`/`#0C1830`, teal `#17B8B0`/`#0E8F89`, numbered kicker + bold title, tile/card layout, footer. The new deck was rebuilt programmatically (`source_code/src/build_deck.py`) because the original consisted of ~600 individual shapes; charts are the real figures from the recorded data.

| New | Original | What changed and why |
|---|---|---|
| 1 | 1 | Subtitle states the extended scope; "first submission July 2026 / extended edition October 2026". |
| 2 | 2, 3 | Motivation and the three constraints merged; added "what this extended work adds". |
| 3 | 3 | Objectives now marked inherited vs new; scope boundaries stated (grey-scale, non-blind, video exploratory). |
| 4 | 4 | Timeline of verified references; **false-positive warning** [4][5]; research gaps; the unsupported "hybrids always win" claim is no longer asserted. |
| 5 | 5 | Embedding pipeline at full size; diagram text corrected ("global DCT", overlap of logo box fixed). |
| 6 | 6 | Extraction pipeline; "semi-blind" corrected to **non-blind**; key contents corrected. |
| 7 | — (new) | Mathematics (equations 1–5) and what follows from them. |
| 8 | 8 (part) | Transformation table T1–T20 (only operations present in the code). |
| 9 | 8 (dataset box) | 100-image dataset, composition, provenance and limits (was 2 images). |
| 10 | 7 | Evaluation design: 14 attacks **plus** the unattacked reference (the original said "15 attacks"), experiments E1–E4/S1/S2/V1, metrics incl. ZNCC. |
| 11 | 9 | Imperceptibility at n = 100; PSNR/SSIM distribution; failure cases (SSIM 0.58 at 35.9 dB). |
| 12 | 10 | Robustness boxplot over 100 images; honest table; "13 of 15 attacks" headline replaced by measured pass rates. |
| 13 | — (new) | Which images fail (contrast/brightness correlations, category heat-map). |
| 14 | 11 | α trade-off redone: 3 panels, 4 attacks, 100 images; the old dual-axis figure explained as an artefact. |
| 15 | 12 (part) | **False-positive controls** — wrong logo decoded with the owner's key: NC 0.975. |
| 16 | 12 | Four failure modes (cropping, equalisation, rotation, near-constant images) with data. |
| 17 | — (new) | Component comparison across libraries (measured). |
| 18 | — (new) | Scheme comparison vs `blind-watermark`, block-DCT and LSB (measured; no claim of superiority). |
| 19 | 13 (video idea) | Exploratory video test, clearly labelled as feasibility only. |
| 20 | — (new) | Ten claims of the first submission checked against the 100-image evidence. |
| 21 | 8 | Implementation quality: 43 tests, seeds, identical re-runs, traceability, how to reproduce. |
| 22 | 13 | Limitations (measured) and prioritised future scope. |
| 23 | 14 | Conclusion with the revised headline numbers; "NC alone is not proof of ownership". |
| 24 | 15 | Reference list rebuilt with verified entries (5 → 17 shown; full list in `research/REFERENCES.md`). |

Removed or changed claims: "13 of 15 attacks held" and "25/30" as headline (now 85.1 % of 1500 trials, 84.1 % excluding the reference); "α ≈ 0.15–0.20 at small PSNR cost" (measured 32.5 / 30.1 dB); "JPEG alignment of the DCT" (the DCT is global); "standard NC > 0.75" (a project convention).
