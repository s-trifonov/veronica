import json
from PyQt5 import QtCore
from PIL import Image

from h2tools.tools_qt import qt_str
from config.gr_support import GraphicsSupport
from config.ver_cfg import Config
import tools.geom as geom
from .scenario_mouse import MouseEventListener
# from model.stroke import detectStrokeCrossings

#=================================
class DetectController(MouseEventListener):
    def __init__(self, master_pre, img_pre, params_line):
        MouseEventListener.__init__(self, img_pre)
        self.mMasterPre = master_pre
        self.mShowGroup = img_pre._getDetectGroup()
        self.mParamsLine = params_line
        self.mMarkupHidden = False
        self.mImageH = None
        self.mLinePoints = None
        self.mLineDetectResults = None
        self.mWorkImage = None
        self.mWorkImagePath = None
        self.mPrevParams = None

    def updateImage(self, image_h):
        if self.mImageH is not image_h:
            self.mImageH = image_h
            self.mMarkupHidden = False
            self.mLinePoints = None
            self.mLineDetectResults = None

    def startDetectLine(self):
        if self.mParamsLine.text() != self.mPrevParams:
            try:
                params = json.loads(self.mParamsLine.text())
                if (isinstance(params, list) and len(params) == 2
                    and all(isinstance(pp, list) and len(pp) == 2
                        and all(isinstance(v, int) for v in pp)
                        for pp in params)):
                    self.mLinePoints = params
                    self._doDetection()
                    self.drawAll()
                    return
            except Exception:
                pass

        self.mLinePoints = [] if self.mImageH is not None else None
        self.mLineDetectResults = None
        self.mParamsLine.setText(qt_str(""))

    def drawAll(self):
        if self.mLinePoints is not None:
            self.getViewPort()._setMarkPoints(self.mLinePoints)
        GraphicsSupport.readyLineDetection(
            self.mShowGroup, self.mLineDetectResults)

    def activate(self):
        self.mMarkupHidden = False
        self.drawAll()
        self.setCursor(QtCore.Qt.ArrowCursor)

    def deactivate(self):
        GraphicsSupport.clearGroup(self.mShowGroup)
        self.getViewPort()._clearMarkPoints()

    DSTEP = Config.STROKE_WIDTH // 2
    def _checkCurMod(self, pos):
        if self.mLinePoints is None or len(self.mLinePoints) == 2:
            self.setCursor(QtCore.Qt.ArrowCursor)
            return False
        assert self.mImageH is not None
        w, h = self.getViewPort().getCurSize()
        if not (self.DSTEP <= pos[0] < w - self.DSTEP and
                self.DSTEP <= pos[1] < h - self.DSTEP) or (
                len(self.mLinePoints) == 1 and
                geom.length(*geom.delta(pos, self.mLinePoints[0])) <
                Config.STROKE_WIDTH):
            self.setCursor(QtCore.Qt.ForbiddenCursor)
            return False
        self.setCursor(QtCore.Qt.CrossCursor)
        return True

    #====================
    def mouseMoveEvent(self, event):
        if self.mMarkupHidden:
            self.setCursor(QtCore.Qt.WhatsThisCursor)
            return
        pos = self.mapPos(event)
        self._checkCurMod(pos)

    def mousePressEvent(self, event):
        if not self.buttonIsLeft(event) and not self.mMarkupHidden:
            self.mMarkupHidden = True
            self.getViewPort().showMarkup(False)
            self.setCursor(QtCore.Qt.WhatsThisCursor)
            return
        pos = self.mapPos(event)
        if not self._checkCurMod(pos):
            return
        if not self.buttonIsLeft(event):
            if len(self.mLinePoints) > 0:
                del self.mLinePoints[-1]
            else:
                self.mLinePoints = None
        else:
            self.mLinePoints.append(pos)
            if len(self.mLinePoints) == 2:
                self._doDetection()
        self.drawAll()

    def mouseReleaseEvent(self, event):
        if self.mMarkupHidden:
            self.mMarkupHidden = False
            self.getViewPort().showMarkup(True)

    #====================
    def _doDetection(self):
        assert self.mImageH is not None
        self.mPrevParams = json.dumps(self.mLinePoints)
        self.mParamsLine.setText(qt_str(self.mPrevParams))
        if self.mWorkImagePath != self.mImageH.getImagePath():
            self.mWorkImagePath = self.mImageH.getImagePath()
            self.mWorkImage = Image.open(self.mWorkImagePath)
        #self.mLineDetectResults = detectStrokeCrossings(
        #    self.mWorkImage, self.mLinePoints[0], self.mLinePoints[1])
        if self.mLineDetectResults is not None:
            for no, det in enumerate(self.mLineDetectResults):
                print("no=", no, det[-1])

