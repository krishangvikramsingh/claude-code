"""
dataset_manifest.py
===================
Declarative list of every *real* source image used in the 100-image evaluation
set, with its origin, hosting-repository licence and category.

IMPORTANT (rights note)
-----------------------
All downloads come from public GitHub repositories (raw.githubusercontent.com)
or from sample-data bundled with common Python packages.  The ``repo_license``
column records the licence of the *hosting repository*.  The copyright status
of an individual photograph is, in most cases, NOT separately documented
upstream.  ``rights_note`` records whatever the upstream project itself states
(e.g. "CC0 by the photographer").  Where nothing is stated the entry says
"not individually documented upstream".  The images are used here solely for
non-commercial academic evaluation of a watermarking algorithm; users who want
to redistribute them must check the upstream terms.

Each entry:  (key, url_or_special, group, repo_license, rights_note, category)
``url_or_special`` is a path relative to https://raw.githubusercontent.com/
unless it starts with "scipy:" (loaded through scipy.datasets).
"""

OCV = "opencv/opencv/4.x/samples/data/"
OCVX = "opencv/opencv_extra/4.x/testdata/"
OXF = OCVX + "cv/detectors_descriptors_evaluation/images_datasets/"
SKI = "scikit-image/scikit-image/v0.26.0/src/skimage/data/"
THR = "mrdoob/three.js/dev/examples/textures/"
PIL = "python-pillow/Pillow/main/Tests/images/"

_APACHE = "Apache-2.0"
_NOT_DOC = "not individually documented upstream"

REAL_IMAGES = [
    # ---- OpenCV samples ---------------------------------------------------
    ("ocv_apple",        OCV + "apple.jpg",        "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_baboon",       OCV + "baboon.jpg",       "OpenCV samples", _APACHE, "classic USC-SIPI 'mandrill' test image; " + _NOT_DOC, "animal"),
    ("ocv_board",        OCV + "board.jpg",        "OpenCV samples", _APACHE, _NOT_DOC, "object_fine_detail"),
    ("ocv_building",     OCV + "building.jpg",     "OpenCV samples", _APACHE, _NOT_DOC, "urban_architecture"),
    ("ocv_butterfly",    OCV + "butterfly.jpg",    "OpenCV samples", _APACHE, _NOT_DOC, "animal"),
    ("ocv_chicky",       OCV + "chicky_512.png",   "OpenCV samples", _APACHE, _NOT_DOC, "animal"),
    ("ocv_fruits",       OCV + "fruits.jpg",       "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_graf1",        OCV + "graf1.png",        "OpenCV samples", _APACHE, "Oxford affine-regions 'graf' image; research use", "urban_architecture"),
    ("ocv_home",         OCV + "home.jpg",         "OpenCV samples", _APACHE, _NOT_DOC, "urban_architecture"),
    ("ocv_left01",       OCV + "left01.jpg",       "OpenCV samples", _APACHE, "calibration-pattern scene (one of 12 near-identical frames; only one kept)", "indoor_person"),
    ("ocv_messi",        OCV + "messi5.jpg",       "OpenCV samples", _APACHE, _NOT_DOC, "person_sports"),
    ("ocv_orange",       OCV + "orange.jpg",       "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_smarties",     OCV + "smarties.png",     "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_starry_night", OCV + "starry_night.jpg", "OpenCV samples", _APACHE, "reproduction of a public-domain painting (van Gogh, 1889)", "painting_art"),
    ("ocv_stuff",        OCV + "stuff.jpg",        "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_rubberwhale",  OCV + "rubberwhale1.png", "OpenCV samples", _APACHE, "Middlebury optical-flow dataset frame; research use", "object"),
    ("ocv_text_motion",  OCV + "text_motion.jpg",  "OpenCV samples", _APACHE, _NOT_DOC, "document_text"),
    ("ocv_imagetext",    OCV + "imageTextN.png",   "OpenCV samples", _APACHE, _NOT_DOC, "document_text"),
    ("ocv_basketball",   OCV + "basketball1.png",  "OpenCV samples", _APACHE, "video frame; " + _NOT_DOC, "indoor_person"),
    ("ocv_blox",         OCV + "blox.jpg",         "OpenCV samples", _APACHE, _NOT_DOC, "object"),
    ("ocv_books",        OCV + "left.jpg",         "OpenCV samples", _APACHE, "left view of a stereo pair (right view omitted); " + _NOT_DOC, "indoor_object"),
    ("ocv_aloe",         OCV + "aloeL.jpg",        "OpenCV samples", _APACHE, "Middlebury stereo dataset (left view only); research use", "plant_object"),
    # ---- OpenCV extra test data ------------------------------------------
    ("ocvx_airplane",    OCVX + "cv/shared/airplane.png",       "OpenCV extra", _APACHE, "classic USC-SIPI 'airplane (F-16)' test image; " + _NOT_DOC, "aerial_vehicle"),
    ("ocvx_monalisa",    OCVX + "cv/cascadeandhog/images/mona-lisa.png", "OpenCV extra", _APACHE, "reproduction of a public-domain painting", "painting_art"),
    ("ocvx_shuttle",     OCVX + "dnn/space_shuttle.jpg",        "OpenCV extra", _APACHE, _NOT_DOC, "aerial_vehicle"),
    ("ocvx_street",      OCVX + "dnn/street.png",               "OpenCV extra", _APACHE, _NOT_DOC, "urban_architecture"),
    ("ocvx_cones",       OCVX + "cv/stereomatching/datasets/cones/im2.png", "OpenCV extra", _APACHE, "Middlebury stereo 'cones' (view 2); research use", "indoor_object"),
    ("ocvx_david",       OCVX + "cv/face/david1.jpg",           "OpenCV extra", _APACHE, "face video frame; " + _NOT_DOC, "person_portrait"),
    ("oxf_bark",         OXF + "bark/img1.png",   "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "texture_natural"),
    ("oxf_bikes",        OXF + "bikes/img1.png",  "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "urban_architecture"),
    ("oxf_boat",         OXF + "boat/img1.png",   "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "urban_architecture"),
    ("oxf_leuven",       OXF + "leuven/img1.png", "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "urban_architecture"),
    ("oxf_trees",        OXF + "trees/img1.png",  "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "natural_scene"),
    ("oxf_ubc",          OXF + "ubc/img1.png",    "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "urban_architecture"),
    ("oxf_wall",         OXF + "wall/img1.png",   "Oxford affine-regions (via OpenCV extra)", _APACHE, "K. Mikolajczyk et al., Oxford VGG; research use", "texture_natural"),
    # ---- darknet (YOLO) sample images ------------------------------------
    ("dkn_dog",          "pjreddie/darknet/master/data/dog.jpg",     "darknet", "YOLO licence (public domain)", _NOT_DOC, "animal"),
    ("dkn_eagle",        "pjreddie/darknet/master/data/eagle.jpg",   "darknet", "YOLO licence (public domain)", _NOT_DOC, "animal"),
    ("dkn_giraffe",      "pjreddie/darknet/master/data/giraffe.jpg", "darknet", "YOLO licence (public domain)", _NOT_DOC, "animal"),
    ("dkn_horses",       "pjreddie/darknet/master/data/horses.jpg",  "darknet", "YOLO licence (public domain)", _NOT_DOC, "animal"),
    ("dkn_kite",         "pjreddie/darknet/master/data/kite.jpg",    "darknet", "YOLO licence (public domain)", _NOT_DOC, "natural_scene"),
    ("dkn_person",       "pjreddie/darknet/master/data/person.jpg",  "darknet", "YOLO licence (public domain)", _NOT_DOC, "natural_scene"),
    ("dkn_scream",       "pjreddie/darknet/master/data/scream.jpg",  "darknet", "YOLO licence (public domain)", "reproduction of a painting (Munch, 1893)", "painting_art"),
    # ---- other open-source repositories ----------------------------------
    ("tv_dog1",          "pytorch/vision/main/gallery/assets/dog1.jpg", "torchvision gallery", "BSD-3-Clause", _NOT_DOC, "animal"),
    ("tv_dog2",          "pytorch/vision/main/gallery/assets/dog2.jpg", "torchvision gallery", "BSD-3-Clause", _NOT_DOC, "animal"),
    ("tfm_dogs",         "tensorflow/models/master/research/object_detection/test_images/image1.jpg", "TensorFlow models", _APACHE, _NOT_DOC, "animal"),
    ("tfm_beach",        "tensorflow/models/master/research/object_detection/test_images/image2.jpg", "TensorFlow models", _APACHE, _NOT_DOC, "natural_scene"),
    ("sam_dog",          "facebookresearch/segment-anything/main/notebooks/images/dog.jpg",       "segment-anything", _APACHE, _NOT_DOC, "indoor_person"),
    ("sam_groceries",    "facebookresearch/segment-anything/main/notebooks/images/groceries.jpg", "segment-anything", _APACHE, _NOT_DOC, "object"),
    ("sam_truck",        "facebookresearch/segment-anything/main/notebooks/images/truck.jpg",     "segment-anything", _APACHE, _NOT_DOC, "urban_architecture"),
    ("mmd_demo",         "open-mmlab/mmdetection/main/demo/demo.jpg", "mmdetection", _APACHE, _NOT_DOC, "natural_scene"),
    ("hf_cats",          "huggingface/transformers/main/tests/fixtures/tests_samples/COCO/000000039769.png", "transformers test fixtures", _APACHE, "COCO val image (Flickr, CC BY 2.0 per COCO terms; attribution per COCO)", "animal"),
    # ---- three.js example textures / environment photos ------------------
    ("thr_park",         THR + "cube/Park2/posx.jpg",                 "three.js examples", "MIT", "cube-map face; texture rights " + _NOT_DOC, "natural_scene"),
    ("thr_bridge",       THR + "cube/Bridge2/posx.jpg",               "three.js examples", "MIT", "cube-map face; texture rights " + _NOT_DOC, "natural_scene"),
    ("thr_castle",       THR + "cube/SwedishRoyalCastle/px.jpg",      "three.js examples", "MIT", "cube-map face (night scene); texture rights " + _NOT_DOC, "urban_architecture"),
    ("thr_pisa",         THR + "cube/pisa/px.png",                    "three.js examples", "MIT", "cube-map face; texture rights " + _NOT_DOC, "urban_architecture"),
    ("thr_milkyway",     THR + "cube/MilkyWay/dark-s_px.jpg",         "three.js examples", "MIT", "cube-map face (near-black sky); texture rights " + _NOT_DOC, "astronomy_space"),
    ("thr_caravaggio",   THR + "758px-Canestra_di_frutta_%28Caravaggio%29.jpg", "three.js examples", "MIT", "reproduction of a public-domain painting (Caravaggio)", "painting_art"),
    ("thr_interior",     THR + "2294472375_24a3b8ef46_o.jpg",         "three.js examples", "MIT", "equirectangular interior panorama (Flickr origin); " + _NOT_DOC, "indoor_object"),
    ("thr_earth",        THR + "planets/earth_atmos_2048.jpg",        "three.js examples", "MIT", "NASA-derived Earth map; " + _NOT_DOC, "scientific_map"),
    ("thr_moonmap",      THR + "planets/moon_1024.jpg",               "three.js examples", "MIT", "lunar surface map; " + _NOT_DOC, "scientific_map"),
    ("thr_hardwood",     THR + "hardwood2_diffuse.jpg",               "three.js examples", "MIT", "wood-floor texture; " + _NOT_DOC, "texture_natural"),
    ("thr_brick",        THR + "brick_diffuse.jpg",                   "three.js examples", "MIT", "brick-wall texture; " + _NOT_DOC, "texture_natural"),
    ("thr_grass",        THR + "terrain/grasslight-big.jpg",          "three.js examples", "MIT", "grass texture; " + _NOT_DOC, "texture_natural"),
    ("thr_lava",         THR + "lava/lavatile.jpg",                   "three.js examples", "MIT", "lava texture; " + _NOT_DOC, "texture_natural"),
    # ---- scikit-image bundled data ----------------------------------------
    ("ski_astronaut",    SKI + "astronaut.png", "scikit-image data", "BSD-3-Clause", "NASA photograph of Eileen Collins (public domain)", "person_portrait"),
    ("ski_brick",        SKI + "brick.png",     "scikit-image data", "BSD-3-Clause", "CC0 (CC0Textures)", "texture_natural"),
    ("ski_camera",       SKI + "camera.png",    "scikit-image data", "BSD-3-Clause", "CC0 by the photographer (Lav Varshney)", "person_portrait"),
    ("ski_cell",         SKI + "cell.png",      "scikit-image data", "BSD-3-Clause", "quantitative phase image of a cell (qpformat)", "scientific_medical"),
    ("ski_chelsea",      SKI + "chelsea.png",   "scikit-image data", "BSD-3-Clause", "CC0 by the photographer (Stefan van der Walt)", "animal"),
    ("ski_clock",        SKI + "clock_motion.png", "scikit-image data", "BSD-3-Clause", "public domain (Stefan van der Walt); motion-blurred", "object"),
    ("ski_coffee",       SKI + "coffee.png",    "scikit-image data", "BSD-3-Clause", "CC0 by the photographer (Rachel Michetti)", "object"),
    ("ski_coins",        SKI + "coins.png",     "scikit-image data", "BSD-3-Clause", "Brooklyn Museum Collection (open collection)", "object"),
    ("ski_grass",        SKI + "grass.png",     "scikit-image data", "BSD-3-Clause", "CC0 (DeviantArt, linolafett)", "texture_natural"),
    ("ski_gravel",       SKI + "gravel.png",    "scikit-image data", "BSD-3-Clause", "CC0 (CC0Textures)", "texture_natural"),
    ("ski_hubble",       SKI + "hubble_deep_field.jpg", "scikit-image data", "BSD-3-Clause", "HubbleSite / NASA image", "astronomy_space"),
    ("ski_ihc",          SKI + "ihc.png",       "scikit-image data", "BSD-3-Clause", "immunohistochemistry micrograph (Center for Microscopy and Image Analysis, Zurich)", "scientific_medical"),
    ("ski_moon",         SKI + "moon.png",      "scikit-image data", "BSD-3-Clause", "low-contrast lunar surface image", "astronomy_space"),
    ("ski_motorcycle",   SKI + "motorcycle_left.png", "scikit-image data", "BSD-3-Clause", "Middlebury stereo dataset (left view only); research use", "indoor_object"),
    ("ski_retina",       SKI + "retina.jpg",    "scikit-image data", "BSD-3-Clause", "CC0 (Wikimedia Commons fundus photograph)", "scientific_medical"),
    ("ski_rocket",       SKI + "rocket.jpg",    "scikit-image data", "BSD-3-Clause", "SpaceX Photos (Flickr); see upstream licence", "aerial_vehicle"),
    # ---- other package sample data -----------------------------------------
    ("skl_china",        "scikit-learn/scikit-learn/main/sklearn/datasets/images/china.jpg",  "scikit-learn", "BSD-3-Clause", "CC BY 2.0, danielbuechele (Flickr)", "urban_architecture"),
    ("skl_flower",       "scikit-learn/scikit-learn/main/sklearn/datasets/images/flower.jpg", "scikit-learn", "BSD-3-Clause", "CC BY 2.0, vultilion (Flickr)", "plant_object"),
    ("mpl_hopper",       "matplotlib/matplotlib/main/lib/matplotlib/mpl-data/sample_data/grace_hopper.jpg", "matplotlib", "PSF-based (matplotlib licence)", "official US Navy photograph (public domain)", "person_portrait"),
    ("scp_face",         "scipy:face",   "scipy.datasets", "BSD-3-Clause", "raccoon image derived from pixnio.com", "animal"),
    ("scp_ascent",       "scipy:ascent", "scipy.datasets", "BSD-3-Clause", "derived from pixnio.com ('accent-to-the-top')", "person_sports"),
    ("iio_bricks",       "imageio/imageio-binaries/master/images/bricks.jpg", "imageio-binaries", "BSD-2-Clause", _NOT_DOC, "texture_natural"),
    ("iio_wikkie",       "imageio/imageio-binaries/master/images/wikkie.png", "imageio-binaries", "BSD-2-Clause", _NOT_DOC, "animal"),
    # ---- Pillow test images -------------------------------------------------
    ("pil_plumeria",     PIL + "flower.jpg",      "Pillow tests", "HPND", _NOT_DOC, "plant_object"),
    ("pil_heather",      PIL + "flower2.jpg",     "Pillow tests", "HPND", _NOT_DOC, "plant_object"),
    ("pil_field",        PIL + "junk_jpeg_header.jpg", "Pillow tests", "HPND", _NOT_DOC, "natural_scene"),
    ("pil_sign",         PIL + "iptc.jpg",        "Pillow tests", "HPND", _NOT_DOC, "urban_architecture"),
    ("pil_cabin",        PIL + "sugarshack_bad_mpo_header.jpg", "Pillow tests", "HPND", _NOT_DOC, "natural_scene"),
    ("pil_coins",        PIL + "xmp_test.jpg",    "Pillow tests", "HPND", _NOT_DOC, "object"),
    ("pil_aircraft",     PIL + "exif_gps_typeerror.jpg", "Pillow tests", "HPND", _NOT_DOC, "aerial_vehicle"),
    ("pil_beach",        PIL + "icc_profile_big.jpg", "Pillow tests", "HPND", _NOT_DOC, "natural_scene"),
    ("pil_mountain",     PIL + "exif-72dpi-int.jpg",  "Pillow tests", "HPND", _NOT_DOC, "natural_scene"),
]

# Images that are deliberately excluded (documented so the choice is auditable)
EXCLUDED = {
    "lena.jpg": "contested provenance/consent; many institutions advise against its use",
    "left02..left14 (OpenCV calibration frames)": "near-identical frames of one calibration scene",
    "aloeR / right.jpg / rubberwhale2 / motorcycle_right": "second view of an already-included stereo pair or frame",
    "meadow_cube.jpg": "2048x12288 strip, not a natural image of a scene",
    "images < 240 px on the short side": "up-sampling to 512 px would make them artificially smooth",
    "Pillow format-edge-case images (hopper_* variants, EXIF/ICC tests)": "same picture in many encodings; not independent content",
    "ultralytics bus.jpg / zidane.jpg": "AGPL-3.0 repository; photographs of identifiable persons with unclear rights",
}
