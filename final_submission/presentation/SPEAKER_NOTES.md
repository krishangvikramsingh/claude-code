# Speaker notes — Final_Presentation.pptx

Target length: ≈ 15–18 minutes for 24 slides (≈ 40–45 s per slide; slides 12, 14, 15 and 18 deserve more time).

## Slide 1 — Title

Opening. This is the extended version of my watermarking project. The first submission tested a hybrid DWT-DCT-SVD scheme on two images. Since then I audited the code, rebuilt the evaluation on 100 unique images, added control experiments, compared the scheme with existing technology, and tried it on real video. I will show what held up, what did not, and what I corrected.

## Slide 2 — Copying an image takes a second — proving who owns it is the hard part

Motivation: images are copied in one click. An invisible watermark carries an ownership signal inside the pixels. Three constraints must hold at once: imperceptible, robust, explainable. The project's third constraint is explainability: every step is a closed-form linear-algebra operation, no learned component. In this extended work I test whether the first two constraints hold at scale.

## Slide 3 — Six objectives — three inherited from the first submission, three new

Objectives one to three are from the first submission: implement, measure imperceptibility, measure robustness. The new ones are: characterise alpha, find and explain failure modes including false positives, and compare with existing technology and video. Scope boundaries matter: grey-scale only, no machine learning, non-blind scheme, video exploratory.

## Slide 4 — From LSB to hybrids — and an old warning about SVD schemes

A short timeline. Spatial LSB marks by van Schyndel et al. 1994 are fragile. Cox et al. 1997 put a spread-spectrum watermark into significant spectral coefficients. Liu and Tan 2002 introduced SVD ownership watermarking; Ganic and Eskicioglu 2004 combined DWT and SVD. Later hybrids cascade DWT, DCT and SVD. The important warning: comments by Zhang and Li in 2005 and Ting in 2005 concern false positives and ambiguity attacks on this family. I verified the bibliographic details of each reference; I did not re-run those papers' experiments. The claim in my first report that hybrids always beat single transforms is a literature trend, not something I tested.

## Slide 5 — Embedding: add the logo's singular values to the host's — once, by the owner

The embedding pipeline: host image, one-level Haar DWT, take the LL band, apply a 2-D DCT to the whole band, take the SVD, add alpha times the singular values of the logo, and invert the transforms. Two corrections to the first submission are visible here: the DCT is global, not block-wise. The result is an 8-bit image that looks like the original; the owner keeps a key.

## Slide 6 — Extraction needs the owner's key — and rebuilds the owner's logo from it

Extraction repeats DWT, DCT and SVD on the received, possibly attacked image and subtracts the stored original singular values, divides by alpha and rebuilds the logo from the key's singular vectors. Second correction: the scheme is non-blind, not semi-blind, because the key contains the original singular values. And note the consequence we will measure later: because the logo's singular vectors are in the key, the extractor returns the key owner's logo whatever singular values it finds.

## Slide 7 — One tunable parameter: add α times the logo's singular values

The mathematics in five lines. Haar DWT gives the approximation band. A global orthonormal DCT-II moves it to a frequency domain. SVD factors the DCT matrix and the logo. The embedding rule adds alpha times the logo's singular values to the host's singular values. Extraction subtracts the stored original singular values and divides by alpha, then rebuilds the logo from the key's singular vectors. Important consequence: the identity of the logo lives in the key, not in the image.

## Slide 8 — Twenty documented operations — only those that exist in the code

Every operation in the code is documented in TRANSFORMATIONS_REFERENCE with its mathematics, parameters, limitations and complexity. The core is T2 to T5. T8 to T17 are the attacks used for testing. T20, video, is new and exploratory. Generic operations such as Sobel, CLAHE or morphology are not in this project and are not claimed.

## Slide 9 — 100 unique images: 94 real, 6 labelled synthetic — rights and provenance recorded

The dataset: 94 real images from open sample collections hosted on GitHub — OpenCV, scikit-image, torchvision, three.js textures and others — plus six synthetic controls. They are grey-standardised, square-cropped and resized to 512. Near duplicates were rejected by a hash, and a test asserts uniqueness. Important caveat: only raw GitHub and PyPI were reachable, so this is a convenience sample, not a benchmark, and rights for most photographs are not documented upstream — I record exactly what upstream says.

## Slide 10 — Seven experiments, 14 attacks plus a reference, four metrics — all seeded and logged

E1 imperceptibility, E2 robustness with fifteen conditions — fourteen attacks plus the unattacked reference, which the first report counted as an attack — under two protocols, E3 an alpha sweep with four attacks, E4 false-positive controls. S1 and S2 are the technology comparisons and V1 is the video test. Metrics: PSNR and SSIM for imperceptibility; NC, ZNCC and BER for the recovered logo. The 0.75 threshold is the project's convention; I could not find a primary literature source for it, and I measure its false-alarm rate in E4.

## Slide 11 — Invisible on typical images — but PSNR alone hides some failures

Across 100 images the mean PSNR is 36.0 dB and mean SSIM 0.992. Notice that PSNR is almost the same for most images, about 35.6 dB, because the added energy is set by the logo's singular values, not by the host. SSIM exposes exceptions: the near-black Milky Way image has PSNR 35.9 but SSIM 0.58, and the checkerboard 0.86. So PSNR alone would have hidden these failures.

## Slide 12 — 85.1 % of trials recovered — strong for compression and filtering, weak for cropping and equalisation

Headline: 1277 of 1500 trials reach NC at least 0.75 when the unattacked reference is included, as in the first submission, and 1177 of 1400 counting only the 14 attacks. Very robust: JPEG, median filter, sharpening, scaling, salt and pepper, blur, mild noise. Moderate: five and fifteen degree rotation, strong noise. Weak: histogram equalisation, 44 percent, and border cropping, 1 percent. The first submission said moderate rotation and scaling had mean NC above 0.93; with 100 images that holds for scaling, 0.938, but not for 5 degree rotation, 0.880.

## Slide 13 — Robustness depends on the image: higher-contrast images lose more under noise and rotation

Across the 100 images, NC after noise and rotation is negatively correlated with image contrast — Spearman rho about minus 0.65 for strong Gaussian noise, minus 0.68 for salt and pepper and minus 0.55 for 15 degree rotation. Histogram equalisation instead correlates with mean brightness. These are associations, with uncorrected p-values and n of 100, not demonstrated causes. By category, the two document-text images are the weakest, portraits and documents are most sensitive to equalisation; several categories have only one to four images so I treat them as descriptive.

## Slide 14 — The α trade-off is real for noise and rotation — but flat for JPEG, so the earlier figure misled

This slide corrects the first submission. Its trade-off figure used two y-axes with the NC axis zoomed to 0.93 to 0.99, and its JPEG simulation truncated floats, which lowered NC only at alpha 0.02. I re-created its conditions exactly and got the same numbers, then showed that rounding removes the dip. With 100 images and four attacks the picture is clear: after JPEG the NC is flat, but under noise, blur and rotation robustness grows with alpha while PSNR falls. For Gaussian noise the pass rate goes from 9 percent at alpha 0.02 to 85 percent at 0.10 and 95 percent at 0.40, while PSNR falls below 30 dB from alpha 0.20.

## Slide 15 — A different logo decoded with the owner's key still scores NC 0.98 — NC does not prove ownership

This is the most important finding. Control C: embed a different logo in the same host and decode with the key of logo A. The extractor returns the key owner's logo, NC 0.975 against 0.977 for the genuine pair. That is the false-positive problem described for SVD schemes in the literature, now measured for this implementation. Controls A and B: unrelated images decoded with a wrong key score 0.37 to 0.40 on average, and about 10 to 13 percent exceed the 0.75 threshold. A claim of ownership therefore needs an additional safeguard such as an image-bound signature; I did not implement one. I also tried embedding the principal component instead; that made things worse, the unwatermarked image still decoded at 0.98.

## Slide 16 — Four failure modes — explained from the data, not hidden

Border cropping: mean NC 0.02; with 43.75 percent of the area zeroed every singular value changes. The first report called this 25 percent cropping; 25 percent of each dimension is 43.75 percent of the area. Histogram equalisation: 44 percent pass; it varies between images, 0.10 for the cameraman and 0.66 for the astronaut in the first submission. Near-constant images: SSIM collapses though PSNR is fine. Rotation: 72 percent pass at 15 degrees; there is no re-registration.

## Slide 17 — Same operation, different libraries: numerically equal, speed rarely matters here

Component benchmark: the same operation on the same input in different libraries, one thread, in memory, warm-up and repeats. Results agree numerically: DCT and SVD to ten to the minus sixteen, Pillow and OpenCV JPEG bit-identical. OpenCV is much faster for the attack operations — about 340 times for the 3 by 3 median — partly because it works on uint8. But the whole 100-image experiment takes about 80 seconds, so changing libraries is not justified on speed. ImageMagick as a command line tool costs about 49 milliseconds per call, dominated by process start-up.

## Slide 18 — Beats LSB and block-DCT at equal PSNR — but not an existing blind block-based hybrid

Scheme-level comparison with the same 4095-bit payload and the same attacks on 30 images. The block-DCT baseline was tuned to match the project's PSNR. LSB is imperceptible but destroyed by any processing. The open-source blind-watermark package, which is also DWT-DCT-SVD but block-based and blind, has lower bit-error rates under most attacks at higher PSNR, 42 against 36 dB. But it is 13 times slower to embed, 18 times slower to extract, and worse under rotation and strong JPEG. Caveat: its YUV design and my channel-wise attacks may favour it. So the project is a simple, explainable, key-based alternative, not a better algorithm.

## Slide 19 — Per-frame embedding survives H.264 and MJPEG re-encoding — feasibility, not a video benchmark

Because the project's future-scope slide mentioned video, I tested it: 60 frames from each of two real clips, read with OpenCV, watermarked frame by frame, each with its own key, re-encoded with FFmpeg as lossless FFV1, H.264 at three quality levels, and MJPEG at two. All 720 decoded frames gave NC at least 0.972. So lossy codecs are not the difficulty. The caveats are important: keys are per frame, about 2 megabytes each; temporal attacks such as frame dropping or re-timing were not tested; and a naive misaligned frame-drop test still gave NC 0.97, presumably because neighbouring frames are similar — another sign that NC does not bind a mark to a frame.

## Slide 20 — What held up and what did not: ten claims of the first submission checked at n = 100

A direct comparison of the first submission's claims with the 100-image evidence. The headline numbers are reproducible and mostly hold. What changed: moderate rotation is weaker than claimed, the alpha trade-off figure was an artefact for JPEG, the block-DCT and semi-blind labels were wrong, the suite is fourteen attacks plus a reference, and — most importantly — extraction does not prove ownership.

## Slide 21 — Tested, seeded and logged: 43 tests, zero failures, identical re-runs

Implementation: the embed and extract numerics are unchanged, so the first submission's numbers remain reproducible — I re-ran its experiment and got the same table within 0.004. Added: input validation, a safe image loader, a dataset builder, a multiprocessing batch runner that records status and time per operation and re-opens every output, seeded attacks, and 43 tests. Bug found during development, for transparency: a debug flag overwrote the metadata file; fixed, with a regression test.

## Slide 22 — Known limits — and the next steps the evidence supports

Limitations: false positives, non-blind key, cropping and rotation, histogram equalisation, grey-scale only, a lossy clean extraction of about 1 percent BER, and a dataset that is a convenience sample. Future work is ordered by evidence: first bind the logo to the image; then block-based redundant embedding for cropping; then geometric re-synchronisation; colour via luminance; and a proper video design with shared or index-aware keys.

## Slide 23 — A transparent scheme that survives everyday processing — but NC alone is not proof of ownership

Conclusion. The scheme is transparent and survives re-compression and filtering well: 85 percent of all trials, 84 percent of attack trials. Imperceptibility is good on typical images with exceptions. The extension changed the story in four ways: the alpha trade-off exists only for harsher attacks, rotation and equalisation are weaker than claimed, a high NC does not prove ownership, and an existing package beats the project on most attacks. What I would do next is bind the logo to the image. Thank you; questions welcome.

## Slide 24 — Verified sources (IEEE style) — status flags in research/REFERENCES.md

References. All bibliographic details were checked against publisher or secondary records; entries that could not be verified were not cited. The full list with verification status is in research/REFERENCES.md. Thank you.

