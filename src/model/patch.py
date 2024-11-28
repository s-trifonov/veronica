from config.messenger import msg

from h2tools.utils import getExceptionValue
import tools.geom as geom
from .cropper import Cropper
from .v_types import VType

#=================================
class PatchDescr:
    def __init__(self, cropper):
        self.mCropper = cropper
        self.reset()

    def reset(self):
        self.mMarkupPoints = None
        self.mMarkupType = None
        self.mChunking = 0
        self.mBlotting = 0
        self.mSelCount = 0
        self.mDirtiness = 0
        self.mFeatures = set()

    def setMarkupPoints(self, points, type, sel_count = 1):
        self.mMarkupPoints = points
        self.mMarkupType = type
        self.mSelCount = sel_count

    def setChunking(self, chunking):
        self.mChunking = chunking

    def getComplexity(self):
        return (self.mSelCount + self.mChunking +
            int(self.mDirtiness > .3) +
            int(self.mBlotting > .05))

    def getMarkupPoints(self):
        return self.mMarkupPoints

    def addDirtiness(self, dirtiness):
        self.mDirtiness += dirtiness

    def addBlotting(self, blotting):
        self.mBlotting += blotting

    def addFeature(self, feature):
        self.mFeatures.add(feature)

    def getReport(self):
        rep = [self.mCropper.getInfo()]
        if self.mSelCount > 0:
            rep.append(f"Selection count: {self.mSelCount}")
        if self.mMarkupType is not None:
            rep.append(f"Markup type: {self.mMarkupType}")
        complexity = self.getComplexity()
        if complexity >= 0:
            rep.append(f"Complexity: {complexity}")
        if self.mChunking > 0:
            rep.append(f"Chunking: {self.mChunking}")
        if self.mDirtiness > 0:
            rep.append(f"Dirtiness: {self.mDirtiness}")
        if self.mBlotting > 0:
            rep.append(f"Blots: {self.mDirtiness}")
        if len(self.mFeatures) > 0:
            rep.append("Features: " + " ".join(sorted(self.mFeatures)))
        return rep

    def toJSon(self):
        ret = {
            "markup-type": self.mMarkupType,
            "complexity": self.getComplexity(),
            "sel-count": self.mSelCount,
            "chunking": self.mChunking,
            "dirtiness": self.mDirtiness,
            "blotting": self.mDirtiness,
            "features": list(sorted(self.mFeatures))}
        info = self.mCropper.toJSon()
        for key, val in info.items():
            ret[key] = val
        if self.mMarkupPoints:
            ret["points"] = list(list(pp) for pp in self.mMarkupPoints)
        return ret

#=================================
class PatchHandler:
    def __init__(self, img_h, center, angle = 0):
        self.mImgH = img_h
        self.mCropper = Cropper(center, angle)
        self.mStatusMessage = msg("vpatch.no.markup")
        self.mPixmap = None
        self.mDescr = None
        self.mError = None

    @classmethod
    def checkIfCenterCorrect(cls, width, height, point):
        return Cropper.checkIfCenterCorrect(width, height, point)

    def getImgH(self):
        return self.mImgH

    def getDescr(self):
        return self.mDescr

    def hasError(self):
        return self.mError is not None

    def getCropper(self):
        return self.mCropper

    def getPoly(self):
        return self.mCropper.getPoly()

    def getPixmap(self):
        return self.mPixmap

    def getMarkupPoints(self):
        return (self.mDescr.getMarkupPoints()
            if self.mDescr is not None else None)

    def getComplexity(self):
        return (self.mDescr.getComplexity()
            if self.mDescr is not None else -1)

    def getReport(self):
        rep = ["Image: " + self.mImgH.getImagePath(),
            self.mCropper.getInfo(),
            "",
            f"Status: {self.mStatusMessage}"]
        if self.mDescr is not None:
            rep += self.mDescr.getReport()
        if self.mError:
            rep.append(self.mError)
        return "\n".join(rep)

    def setupImage(self, pixmap):
        self.mPixmap = pixmap

    def setupMarkup(self, markup_path_sec):
        self.mStatusMessage = "In work"
        try:
            self.mDescr = self._setupMarkup(markup_path_sec)
        except Exception:
            self.mStatusMessage = msg("vpatch.markup.error")
            self.mError = getExceptionValue()

    def _setupMarkup(self, markup_path_sec):
        descr = PatchDescr(self.mCropper)

        selection = []
        for ptype, points in markup_path_sec:
            tp_descr = VType.getTypeDescr(ptype)
            if tp_descr.getGeomType() == "spline":
                points = geom.splineToPoly(points, tp_descr.isClosed())
            if tp_descr.isAreaType():
                self._evalAreaPath(descr, tp_descr, points)
            else:
                self._evalCurvePath(descr, tp_descr, points, selection)

        #geom.setDebugSegments(self.mCropper.mapPointsToGlobal(points)
        #    for _, _, points in segments)

        if len(selection) == 0:
            self.mStatusMessage = msg("vpatch.markup.empty")
            return descr
        if len(selection) == 1:
            idx = 0
            self.mStatusMessage = msg("vpatch.markup.one")
        else:
            self.mStatusMessage = msg("vpatch.markup.colision",
                len(selection))
            idx = self.mCropper.selectLine(
                [line for _, line, _ in selection])
        m_type, m_points, _ = selection[idx]
        descr.setMarkupPoints(m_points, m_type, len(selection))
        return descr

    def _evalAreaPath(self, p_descr, tp_descr, points):
        area = self.mCropper.measureArea(points)
        if area > 0:
            p_descr.addFeature(tp_descr.getReducedType())
            if tp_descr.getType() == "dirt":
                p_descr.addDirtiness(area)
            elif tp_descr.getType() == "blot":
                p_descr.addBlotting(area)

    def _evalCurvePath(self, p_descr, tp_descr, points, selection):
        chunks = self.mCropper.cutCurve(points, tp_descr.isClosed())
        if chunks is None or len(chunks) == 0:
            return
        p_descr.addFeature(tp_descr.getReducedType())
        n_chunks = 0
        for ch in chunks:
            line = self.mCropper.adaptChunk(ch)
            if line is None:
                n_chunks += 1
            else:
                selection.append((tp_descr.getReducedType(), line, ch))
        if n_chunks > 0:
            p_descr.addFeature("chunks")
            p_descr.setChunking(n_chunks)
