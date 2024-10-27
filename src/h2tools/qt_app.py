#import sys
from PyQt5 import QtCore, QtGui

from config.qss import COMMON_STYLE_SHEET
from h2tools.utils import makeFileURL
from .ui_ctrl import QT_UIController
from .ui_persist import UIPersistPropertiesHandler
#=========================================
class QT_Application:
    def __init__(self, qt_app, name, profile_path, src_path,
            base_url = None, pp_no_save = False):
        self.mQTApp         = qt_app
        self.mName          = name
        self.mProfilePath   = profile_path
        self.mSrcPath       = src_path
        self.mCachedIcons   = dict()
        self.mCachedPixmaps = dict()
        self.mUIControllers = dict()
        self.mUrlBaseDir    = base_url
        if self.mUrlBaseDir is None:
            self.mUrlBaseDir = makeFileURL(self.getSrcPath(""))
        self.mUrlImgDir      = self.mUrlBaseDir + "/icons"
        if profile_path:
            self.mPPHandler     = UIPersistPropertiesHandler(self, pp_no_save)
        else:
            self.mPPHandler     = None
        self.mQTApp.setStyleSheet(COMMON_STYLE_SHEET)

    def getURL_BaseDir(self):
        return self.mUrlBaseDir

    def getURL_ImageDir(self):
        return self.mUrlImgDir

    def getQTApp(self):
        return self.mQTApp

    def getName(self):
        return self.mName

    def getPPHandler(self):
        return self.mPPHandler

    def execute(self):
        return self.mQTApp.exec_()

    def getSrcPath(self, fname, subdir = None, extension = None):
        ret = self.mSrcPath + "/"
        if subdir:
            ret += subdir + "/"
        ret += fname
        if extension:
            ret += "." + extension
        return ret

    def getProfilePath(self, fname):
        return self.mProfilePath + "/" + fname

    def getIcon(self, fname):
        if fname not in self.mCachedIcons:
            self.mCachedIcons[fname] = QtGui.QIcon(
                self.getSrcPath(fname, subdir="icons"))
        return self.mCachedIcons[fname]

    def getUIController(self, name):
        if name not in self.mUIControllers:
            self.mUIControllers[name] = QT_UIController(self, name)
        return self.mUIControllers[name]

    def getPixmap(self, fname):
        if fname not in self.mCachedPixmaps:
            self.mCachedPixmaps[fname] = QtGui.QPixmap(
                self.getSrcPath(fname, subdir="icons"))
        return self.mCachedPixmaps[fname]

    def makeCopyAction(self, top_window):
        self.mQTApp.postEvent(top_window, QtGui.QKeyEvent(
            QtGui.QKeyEvent.KeyPress, 0x43, QtCore.Qt.ControlModifier))
        self.mQTApp.postEvent(top_window, QtGui.QKeyEvent(
            QtGui.QKeyEvent.KeyRelease, 0x43, QtCore.Qt.ControlModifier))
