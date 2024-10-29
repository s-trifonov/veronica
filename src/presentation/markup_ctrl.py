from config.gr_support import GraphicsSupport
from config.ver_cfg import Config
import tools.geom as geom
from model.markup_path import MarkupPath
from .scenario_mouse import MouseScenario_NewPath, MouseScenario_Generic

#=================================
class _PathHandler:
    def __init__(self, idx, type, points):
        self.mIdx = idx
        self.mPath = MarkupPath(type, points)
        self.mPoly = self.mPath.drawPoly()
        self.mGrItem = None

    def reserveGrItem(self, view_port):
        self.mGrItem = view_port._reservePolygon()

    def freeGrItem(self, view_port):
        view_port._freePolygon(self.mGrItem)
        self.mGrItem = None

    def draw(self, as_hot = False, view_poly = None):
        if view_poly is None:
            view_poly = self.mPoly
        if view_poly is None:
            self.mGrItem.hide()
            return
        GraphicsSupport.readyPolygon(self.mGrItem, view_poly,
            self.mPath.getType(), self.mPath.isClosed(), as_hot)
        self.mGrItem.show()

    def getIdx(self):
        return self.mIdx

    def getPath(self):
        return self.mPath

    def distToPoint(self, pp):
        return geom.distToPoly(pp, self.mPoly, self.mPath.isClosed())

#=================================
class MarkupPathController(MouseScenario_Generic):
    def __init__(self, master_pre, img_pre):
        MouseScenario_Generic.__init__(self, img_pre)
        self.mMasterPre = master_pre
        self.mMarkupHidden = False
        self.mPathList = None
        self.mCurPathH = None
        self.mHotPathIdx = None
        self.mNewPathCtrl = None
        self.mIsActive = False
        self.reload()

    def isActive(self):
        return self.mIsActive

    def getPathCount(self):
        return len(self.mPathList)

    def _getCurPathH(self):
        if (not self.mIsActive or self.mNewPathCtrl is not None):
            return None
        return self.mCurPathH

    def getCurPathIdx(self):
        path_h = self._getCurPathH()
        if path_h is None:
            return None
        return path_h.getIdx()

    def getCurPath(self):
        path_h = self._getCurPathH()
        if path_h is None:
            return None
        return path_h.getPath()

    def getNewPath(self):
        if not self.mIsActive or self.mNewPathCtrl is None:
            return None
        return self.mNewPathCtrl.getPath()

    def startNewPath(self, vtype):
        assert self.mIsActive
        if self.mNewPathCtrl is not None:
            self.mNewPathCtrl.deactivate()
        self.mNewPathCtrl = NewPathSubController(
            self.mMasterPre, self.getViewPort(), MarkupPath(vtype))
        self._curGrPoints()

    def clearNewPath(self):
        if self.mNewPathCtrl is not None:
            self.mNewPathCtrl.deactivate()
        self.mNewPathCtrl = None
        self._curGrPoints()

    def reload(self, path_info_seq=None, cur_idx=None):
        self.setCurMod(None)
        if path_info_seq is None:
            self.mPathList = []
        else:
            self.mPathList = [_PathHandler(idx, *path_info)
                for idx, path_info in enumerate(path_info_seq)]
        self.mCurPathH = (self.mPathList[cur_idx] if cur_idx is not None and
            0 <= cur_idx < len(self.mPathList) else None)
        if self.mIsActive:
            self._reserveGr()
            self.drawAll()
        if self.mIsActive:
            self.drawAll()

    def _reserveGr(self):
        self.getViewPort()._clearPolygons()
        for path_h in self.mPathList:
            path_h.reserveGrItem(self.getViewPort())

    def _freeGr(self):
        for path_h in self.mPathList[::-1]:
            path_h.freeGrItem(self.getViewPort())

    def _curGrPoints(self):
        if self.mCurPathH is None or self.mNewPathCtrl is not None:
            self.getViewPort()._clearPoints()
            return
        cur_path = self.mCurPathH.getPath()
        self.getViewPort()._setPoints(
            cur_path.getPoints(), cur_path.getType())

    def drawAll(self):
        self.mHotPathIdx = None
        for path_h in self.mPathList:
            path_h.draw()
        self._curGrPoints()

    def subScenario(self):
        assert self.mIsActive
        return self.mNewPathCtrl

    def onActivate(self):
        assert self.mIsActive is False
        self.mIsActive = True
        self.mMarkupHidden = False
        self._reserveGr()
        self.drawAll()

    def onDeactivate(self):
        assert self.mIsActive
        self.mIsActive = False
        if self.mNewPathCtrl is not None:
            self.mNewPathCtrl.deactivate()
            self.mNewPathCtrl = None
        self._freeGr()

    def locateCur(self, pp):
        if len(self.mPathList) == 0:
            return None
        dd, idx = min((path_h.distToPoint(pp), path_h.getIdx())
            for path_h in self.mPathList)
        if dd <= Config.MIN_DIST:
            if idx == self.mHotPathIdx:
                return self.mHotPathIdx
        else:
            idx = None
        if self.mHotPathIdx is not None:
            self.mPathList[self.mHotPathIdx].draw()
        self.mHotPathIdx = idx
        if (self.mHotPathIdx is not None
                and self.mHotPathIdx != self.getCurPathIdx()):
            self.mPathList[self.mHotPathIdx].draw(True)
        return idx

    def setCurPath(self, idx, scroll_to=False):
        if idx is None:
            if self.mCurPathH is None:
                return
        elif idx == self.getCurPathIdx():
            return

        if self.mHotPathIdx is not None:
            self.mPathList[self.mHotPathIdx].draw()
            self.mHotPathIdx = None

        if idx is None or not 0 <= idx < len(self.mPathList):
            self.mCurPathH = None
        else:
            self.mCurPathH = self.mPathList[idx]
            self._curGrPoints()
            if scroll_to:
                points = self.getCurPath().getPoints()
                self.getViewPort().scrollToPoints(points[0], points[-1])
        self.mMasterPre.needsUpdate()

    def onTouchCurPath(self):
        if self.mCurPathH is not None:
            self.mCurPathH.draw()
            if self.mHotPathIdx == self.mCurPathH.getIdx():
                self.mHotPathIdx = None
        if self.mHotPathIdx is not None:
            self.mPathList[self.mHotPathIdx].draw()
            self.mHotPathIdx = None

    def onPathChange(self):
        assert self.mCurPathH is not None
        self.mMasterPre.pathChanged(
            self.mCurPathH.getPath(), self.mCurPathH.getIdx())

    def viewPathPoly(self, view_poly):
        if self.mCurPathH is not None:
            self.mCurPathH.draw(True, view_poly)

    def onClick(self, event):
        if not self.buttonIsLeft(event) and not self.mMarkupHidden:
            self.mMarkupHidden = True
            self.getViewPort().showMarkup(False)

    def onUnclick(self, event):
        if self.mMarkupHidden:
            self.mMarkupHidden = False
            self.getViewPort().showMarkup(True)

    def mouseBlocked(self):
        return self.mMarkupHidden

#=================================
class NewPathSubController(MouseScenario_NewPath):
    def __init__(self, master_pre, img_pre, the_pass):
        MouseScenario_NewPath.__init__(self, img_pre, the_pass)
        self.mMasterPre = master_pre
        self.mPolyItem = self.getViewPort()._reservePolygon()
        self.mOpPolyUsed = False

    def getType(self):
        return "new-path"

    def changePathType(self, vtype):
        if self.getPath().canChangeType(vtype):
            self.getPath().changeType(vtype)
            self.onPathChange()

    def onActivate(self):
        self.onPathChange()

    def onDeactivate(self):
        self.getViewPort()._freePolygon(self.mPolyItem)
        self.getViewPort()._clearPoints()
        self.mPolyItem = None

    def onPathChange(self):
        self.getViewPort()._setPoints(self.getPath().getPoints(),
            self.getPath().getType())
        if self.getPath().isComplete():
            self.mMasterPre.newPathCompleted(self)
        else:
            self._viewPoly(self.getPath().drawPoly())

    def _viewPoly(self, view_poly):
        if view_poly in (None, True):
            self.mPolyItem.hide()
        else:
            GraphicsSupport.readyPolygon(
                self.mPolyItem, view_poly, self.getPath().getType(),
                self.getPath().isClosed(), is_current=True)
            self.mPolyItem.show()

    def viewPoly(self, view_poly):
        self.mOpPolyUsed = True
        self._viewPoly(view_poly)
