#import sys

class Config:
    #=================================
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

    VIS_DELTA = 5
    MIN_DIST = 20
    MIN_DIAMETER = 50
    MAX_PATH_POINTS = 15
    SPLINE_VIS_SEG = 20
