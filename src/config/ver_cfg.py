#import sys
#=================================
class Config:
    IMG_CACHE_SIZE = 10

    DEFAULT_IMAGE_HEIGHT = 1000
    DEFAULT_IMAGE_WIDTH = 1000


    VERSION             = "0.0.1"

    DEBUG_MODE          = False
    UI_CONTEXTS         = set()

    DEBUG_HTML_PATH     = "./debug.html"

    IN_HTTP_PORT = 12345

    MAX_STORING_EDIT_STEPS = 100

    PREFS_FILE = "veronica-prefs.js"
    PREFS_DEFAULT = {
        "ext-edit":         "notepad2",
        "file-kbd":         "keyboard.kbd"
    }

    TOO_SMALL = 1E-10

    SMP_ROUND = "learn"

    SMP_KEY = "V0"
    SMP_UNREADY_FREE_COUNT = 5

    VIS_DELTA = 5
    MIN_DIST = 20
    MIN_DIAMETER = 50
    MAX_PATH_POINTS = 15
    SPLINE_VIS_SEG = 20

    STROKE_WIDTH = 16

    PATCH_HALF_SIZE = 64
    PATCH_SIZE = PATCH_HALF_SIZE * 2
    PATCH_MIN_DIST = 4
    PATCH_LONG_CROSS = 8
    PATCH_TOO_SHORT_CROSS = 1

    TRAIN_PACK_SIZE = 100
    TRAIN_PACK_COMPLEX_MD = 1
    TRAIN_PACK_MAX_ITERATIONS = 300
