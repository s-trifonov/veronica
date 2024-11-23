from config.messenger import msg

from h2tools.utils import getExceptionValue
import tools.geom as geom
from .cropper import Cropper
from .v_types import VType
#=================================
class PatchInfo:
    def __init__(self, img_h, center, angle = 0):
        self.mImgH = img_h
        self.mCropper = Cropper(center, angle)
        self.mStatusMessage = msg("vpatch.no.markup")
        self.mPixmap = None
        self.mMarkupPoints = None
        self.mMarkupType = None
        self.mComplexity = -1
        self.mDirtiness = -1
        self.mChunking = -1
        self.mSelCount = -1
        self.mFeatures = None
        self.mError = False

    @classmethod
    def checkIfCenterCorrect(cls, width, height, point):
        return Cropper.checkIfCenterCorrect(width, height, point)

    def getImgH(self):
        return self.mImgH

    def hasError(self):
        return self.mError is not None

    def getCropper(self):
        return self.mCropper

    def getPoly(self):
        return self.mCropper.getPoly()

    def getPixmap(self):
        return self.mPixmap

    def getMarkupPoints(self):
        return self.mMarkupPoints

    def getReport(self):
        rep = ["Image: " + self.mImgH.getImagePath(),
            self.mCropper.getInfo(),
            "",
            f"Status: {self.mStatusMessage}"]
        if self.mMarkupType is not None:
            rep.append(f"Markup type: {self.mMarkupType}")
        if self.mComplexity >= 0:
            rep += ["",
                f"Selection count: {self.mSelCount}",
                f"Complexity: {self.mComplexity}",
                f"Dirtiness: {self.mDirtiness}",
                f"Chunking: {self.mChunking}"]
        if self.mFeatures is not None and len(self.mFeatures) > 0:
            rep.append("Features: " + " ".join(sorted(self.mFeatures)))
        if self.mError:
            rep.append(self.mError)
        return "\n".join(rep)

    def setupImage(self, pixmap):
        self.mPixmap = pixmap

    def setupMarkup(self, markup_path_sec):
        self.mStatusMessage = "In work"
        try:
            self._setupMarkup(markup_path_sec)
        except Exception:
            self.mStatusMessage = msg("vpatch.markup.error")
            self.mError = getExceptionValue()
            self.mMarkupPoints = None
            self.mMarkupType = None
            self.mComplexity = 0
            self.mSelCount = 0
            self.mDirtiness = 0
            self.mChunking = 0
            self.mFeatures = {"error"}

    def _setupMarkup(self, markup_path_sec):
        self.mMarkupPoints = None
        self.mMarkupType = None
        self.mComplexity = 0
        self.mSelCount = 0
        self.mDirtiness = 0
        self.mChunking = 0
        self.mFeatures = set()

        selection = []
        for ptype, points in markup_path_sec:
            tp_descr = VType.getTypeDescr(ptype)
            if tp_descr.getGeomType() == "spline":
                points = geom.splineToPoly(points, tp_descr.isClosed())
            if tp_descr.isAreaType():
                self._evalAreaPath(tp_descr, points)
            else:
                self._evalCurvePath(tp_descr, points, selection)

        #geom.setDebugSegments(self.mCropper.mapPointsToGlobal(points)
        #    for _, _, points in segments)

        if len(selection) == 0:
            self.mStatusMessage = msg("vpatch.markup.empty")
            return
        if len(selection) == 1:
            idx = 0
            self.mStatusMessage = msg("vpatch.markup.one")
        else:
            self.mStatusMessage = msg("vpatch.markup.colision",
                len(selection))
            idx = self.mCropper.selectLine(
                [line for _, line, _ in selection])
        self.mMarkupType, self.mMarkupPoints, _ = selection[idx]

    def _evalAreaPath(self, tp_descr, points):
        area = self.mCropper.measureArea(points)
        if area > 0:
            self.mFeatures.add(tp_descr.getType())
            if tp_descr.getType() == "dirt":
                self.mDirtiness += area
                self.mComplexity += int(area * 4)
            elif tp_descr.getType() == "blot":
                self.mComplexity += 1

    def _evalCurvePath(self, tp_descr, points, selection):
        chunks = self.mCropper.cutCurve(points, tp_descr.isClosed())
        if chunks is None or len(chunks) == 0:
            return
        self.mFeatures.add(tp_descr.getType())
        for ch in chunks:
            self.mComplexity += 1
            line = self.mCropper.adaptChunk(ch)
            if line is None:
                self.mChunking += 1
            else:
                selection.append((tp_descr.getType(), line, ch))
                self.mSelCount += 1
