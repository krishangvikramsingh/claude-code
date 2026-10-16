# Digital Image Watermarking (hybrid DWT–DCT–SVD) — improved submission package

Project of Krishang Vikram Singh (NMIMS MPSTME, Image and Video Processing). This package keeps the original project and adds a code audit,
a 100-image evaluation, a technology comparison, a literature review, a rewritten report and an improved presentation.

## Start here
| What | Where |
|---|---|
| **Report** (editable / PDF) | `report/Final_Project_Report.docx`, `report/Final_Project_Report.pdf` |
| **Presentation** (editable / PDF / speaker notes) | `presentation/Final_Presentation.pptx`, `presentation/Final_Presentation.pdf`, `presentation/SPEAKER_NOTES.md` |
| **Research paper + code in one Word file (teacher's submission, named by roll number)** | `paper/B106.docx` (PDF copy: `paper/B106.pdf`) |
| What was found in the original code | `documentation/PROJECT_AUDIT.md` |
| Every transformation, with maths | `documentation/TRANSFORMATIONS_REFERENCE.md` |
| How the experiments were run | `documentation/EXPERIMENT_METHODOLOGY.md` |
| What changed and known limitations | `documentation/CHANGELOG.md` |
| Technology comparison | `research/TECHNOLOGY_COMPARISON.md` |
| Literature review and verified references | `research/LITERATURE_REVIEW.md`, `research/REFERENCES.md` |
| Dataset, attribution | `data/README.md`, `data/metadata.csv`, `data/original/` |
| Raw and summarised results | `results/` (`results_*.csv`, `tables/`, `run_summary.json`, `analysis_summary.json`) |
| Figures | `visualizations/` |
| Final validation checklist | `documentation/VALIDATION_CHECKLIST.md` |
| Original files (untouched) | `source_code/original_backup/`, `report/Original_Report.docx`, `presentation/Original_Presentation.pptx` |

## Headline results (100 images, α = 0.10; all from `results/`)
* Imperceptibility: mean PSNR 35.99 dB, mean SSIM 0.992 (3 images below SSIM 0.98).
* Robustness (NC ≥ 0.75): 85.1 % of 1500 trials (14 attacks + an unattacked reference; 84.1 % of the 1400 attack trials alone); ≥ 95 % for JPEG Q≥20, median, blur, 0.5× scaling, sharpening and mild noise (σ²=0.005) or 2 % salt-and-pepper; 72 % for 15° rotation; 44 % for histogram equalisation; 1 % for border cropping.
* **False-positive problem measured:** a different logo decoded with the owner's key gives NC 0.975 (genuine 0.977); unrelated images exceed NC 0.75 in 10–13 % of controls.
* Against existing technology: more robust than LSB/block-DCT at equal PSNR, **not** better than the `blind-watermark` library (lower BER, higher PSNR, but 13× slower and weaker under rotation).

## Reproduce
```
pip install -r source_code/requirements.txt
cd source_code/src
python build_dataset.py && python run_batch_experiment.py && python analysis.py
python benchmark_tech.py && python analysis_tech.py && python video_demo.py
cd ../.. && python -m pytest tests -q          # 43 tests
```
Details: `documentation/EXPERIMENT_METHODOLOGY.md`. Needs network for the dataset download (raw.githubusercontent.com), `ffmpeg` for the video test, ImageMagick for one benchmark row.

## Layout
```
source_code/{src,original_backup,config.json,requirements.txt}   tests/   data/{original,metadata.csv,README.md}
outputs/watermarked   results/   visualizations/   research/   documentation/   report/   presentation/
```
