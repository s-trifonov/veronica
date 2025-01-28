import sys, os, gc
from cachetools import LRUCache
from PyQt5 import QtGui

from config.ver_cfg import Config
from .utils import FileControlHandler, getExceptionValue
#=================================
class PixmapHandler:
    def __init__(self, pool, filename, pixmap):
        self.mPool     = pool
        self.mFileName = filename
        self.mPixmap   = pixmap
        self.mFControl = FileControlHandler(filename, "image")
        self.mIsOK     = True

    def checkIt(self):
        if not self.mIsOK:
            return False
        self.mIsOK = not self.mFControl.hasConflict(True)
        if not self.mIsOK:
            self.mPool._unsubscribe(self.mFileName, self)
        return self.mIsOK

    def getPixmap(self):
        return self.mPixmap

    def getSize(self):
        return self.mPixmap.width(), self.mPixmap.height()
#=================================
class ImagePool:
    def __init__(self, size):
        self.mImgCache = LRUCache(maxsize = size)

    def _loadPixmap(self, full_fname, n_att):
        pixmap = QtGui.QPixmap(full_fname)
        if not pixmap.isNull():
            ret = PixmapHandler(self, full_fname, pixmap)
            self.mImgCache[full_fname] = ret
            return ret
        if n_att > 0:
            if Config.DEBUG_MODE:
                print("Drop pixmap cache, attempt=%d", n_att,
                    file = sys.stderr)
            self.mImgCache.clear()
            gc.collect()
        return None

    def _unsubscribe(self, full_fname, pixmap_h):
        if self.mImgCache.get(full_fname) is pixmap_h:
            del self.mImgCache[full_fname]

    def getPixmapHandler(self, full_fname):
        pixmap_h = self.mImgCache.get(full_fname)
        if pixmap_h is not None and pixmap_h.checkIt():
            return pixmap_h
        if full_fname in self.mImgCache:
            del self.mImgCache[full_fname]
        if not os.path.exists(full_fname):
            return None
        for n_att in range(2, -1, -1):
            try:
                pixmap_h = self._loadPixmap(full_fname, n_att)
                if pixmap_h is not None:
                    return pixmap_h
            except Exception:
                getExceptionValue()
        print("Pixmap is null: %s" % full_fname, file = sys.stderr)
        return None

        ret = self.mPixmapCache.get(full_fname)
        n_attempts = 0
        while ret is None:
            try:
                ret = QtGui.QPixmap(full_fname)
                if ret.isNull():
                    if Config.DEBUG_MODE:
                        print("Drop pixmap cache, attempt=%d", n_attempts)
                    self.mPixmapCache.clear()
                    gc.collect()
                    if n_attempts < 3:
                        n_attempts += 1
                        ret = None
                        continue
                if ret.isNull():
                    print("Pixmap is null: %s" % full_fname, file = sys.stderr)
                else:
                    self.mPixmapCache[full_fname] = ret
            except Exception:
                getExceptionValue()
                ret = True
        return ret
