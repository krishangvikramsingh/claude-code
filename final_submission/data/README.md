# Dataset: 100 unique source images

Built by `source_code/src/build_dataset.py` (reproducible; downloads cached in `data/source_images/`, which is not committed). `metadata.csv` has one row per image with the columns required by the task (ID, original filename, source URL, licence, dimensions, channels, format, file size, category, applicable operations, processing status) plus SHA-256 of the source file, brightness/contrast classes and the per-image attack counts written back by the experiment runner.

* **100 images = 94 real + 6 synthetic controls.** All 100 are unique: near-duplicates were rejected with a 64-bit difference hash (Hamming ≤ 6) and the test `tests/test_dataset_and_results.py::test_exactly_100_unique_images` asserts pixel-level uniqueness.
* Standardisation (identical for all): grey (BT.601) → centre-crop to a square → Lanczos resize to 512×512 → 8-bit PNG in `original/`. Original width/height/mode/format are kept in `metadata.csv`.
* **Diversity actually obtained:** natural scenes, animals, urban/architecture, objects, textures, indoor scenes, portraits, paintings, document text, astronomy, medical/microscopy, maps, aerial vehicles; brightness: mid 87, dark 7, bright 6; contrast: medium 62, low 19, high 19. Source images have a shortest side of 240 px and a longest side of 4096 px; **all are standardised to grey**, so *colour* diversity is not part of the test (the scheme is grey-only).
* **Limits:** 94 real images from open GitHub-hosted sample sets is a convenience sample, not a benchmark such as USC-SIPI/COCO; several categories have only 1–4 images, so per-category numbers are descriptive. Only `raw.githubusercontent.com` and PyPI were reachable when the set was built, which is why Wikimedia/Flickr/benchmark sites are not used.

## Composition by category

| category | images |
|---|---|
| animal | 14 |
| urban_architecture | 13 |
| object | 12 |
| texture_natural | 10 |
| natural_scene | 10 |
| synthetic_control | 6 |
| aerial_vehicle | 4 |
| person_portrait | 4 |
| indoor_object | 4 |
| painting_art | 4 |
| plant_object | 3 |
| scientific_medical | 3 |
| indoor_person | 3 |
| astronomy_space | 3 |
| scientific_map | 2 |
| document_text | 2 |
| person_sports | 2 |
| object_fine_detail | 1 |

## Sources, hosting-repository licences and rights notes

The *repository* licence is **not** a statement about each photograph; the third column records what the upstream project itself says about the pictures. Use of the images here is limited to non-commercial academic evaluation of an algorithm. Do not redistribute `data/original` beyond that without checking upstream terms.

| source group | hosting-repository licence | images |
|---|---|---|
| OpenCV samples | Apache-2.0 | 22 |
| scikit-image data | BSD-3-Clause | 16 |
| three.js examples | MIT | 13 |
| Pillow tests | HPND | 8 |
| Oxford affine-regions (via OpenCV extra) | Apache-2.0 | 7 |
| darknet | YOLO licence (public domain) | 7 |
| OpenCV extra | Apache-2.0 | 6 |
| segment-anything | Apache-2.0 | 3 |
| torchvision gallery | BSD-3-Clause | 2 |
| scipy.datasets | BSD-3-Clause | 2 |
| imageio-binaries | BSD-2-Clause | 2 |
| scikit-learn | BSD-3-Clause | 2 |
| matplotlib | PSF-based (matplotlib licence) | 1 |
| TensorFlow models | Apache-2.0 | 1 |
| mmdetection | Apache-2.0 | 1 |
| transformers test fixtures | Apache-2.0 | 1 |

Per-image attribution (key, exact URL, rights note) is in `metadata.csv` (`source_url`, `rights_note`). Highlights where upstream states a licence: scikit-image CC0 images (`ski_brick`, `ski_camera`, `ski_chelsea`, `ski_coffee`, `ski_grass`, `ski_gravel`, `ski_retina`), NASA public domain (`ski_astronaut`, `ski_hubble`), scikit-learn `china.jpg`/`flower.jpg` **CC BY 2.0** (attribution: Flickr users *danielbuechele* and *vultilion*), COCO image `hf_cats` **CC BY 2.0 per COCO terms** (attribution to the Flickr author required — not individually verified), Oxford affine-regions images (K. Mikolajczyk et al., research use), Middlebury stereo/flow images (research use). The Pillow test images, OpenCV samples, darknet, torchvision, segment-anything, mmdetection, TensorFlow-models and three.js textures carry no per-image rights statement upstream (marked *not individually documented upstream*).

## Synthetic controls (labelled `synthetic_control`, `is_synthetic = 1`)

Generated with a fixed seed by `build_dataset.py`; they are **not** real-world photographs and form a separate stratum:

* `image_095` syn_hgradient: horizontal linear gradient 0-255
* `image_096` syn_radial: radial gradient (smooth, low detail)
* `image_097` syn_grating: 2-D sinusoidal grating (periodic texture)
* `image_098` syn_white_noise: white Gaussian noise, mean 128 / std 40
* `image_099` syn_lowcontrast: smooth noise, mean 128 / std 8 (very low contrast)
* `image_100` syn_checker: 32-px checkerboard (hard edges)

## Excluded candidates (audit trail)

* lena.jpg: contested provenance/consent; many institutions advise against its use
* left02..left14 (OpenCV calibration frames): near-identical frames of one calibration scene
* aloeR / right.jpg / rubberwhale2 / motorcycle_right: second view of an already-included stereo pair or frame
* meadow_cube.jpg: 2048x12288 strip, not a natural image of a scene
* images < 240 px on the short side: up-sampling to 512 px would make them artificially smooth
* Pillow format-edge-case images (hopper_* variants, EXIF/ICC tests): same picture in many encodings; not independent content
* ultralytics bus.jpg / zidane.jpg: AGPL-3.0 repository; photographs of identifiable persons with unclear rights
* Skipped at build time: `tfm_beach` (near-duplicate of `dkn_kite`), `pil_heather` (300×225 < 240 px) — see `build_log.json`.

## Reproduce

```
cd source_code/src
python build_dataset.py        # downloads, standardises, writes data/original + metadata.csv
```
If an upstream file is moved or deleted the builder logs it and continues (it never substitutes other images), and `--target` then yields fewer than 100 images — the exit code is non-zero in that case.
